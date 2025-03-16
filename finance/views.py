import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum
from finance.forms import CategoryForm, TransactionForm
from finance.models import User, Account, Category, Transaction, Currency, Budget
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
import traceback
import calendar

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')

        # Basic validation
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return redirect('register')

        # Create new user
        try:
            user = User.objects.create(
                username=email, 
                email=email,
                password=make_password(password1)
            )
            auth_login(request, user) 
            messages.success(request, 'Registration successful!')
            return redirect('detail')  # Go to home page
        except Exception as e:
            messages.error(request, 'Registration failed')
            return redirect('register')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            auth_login(request, user)
            return redirect('detail') 
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('login')
            
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def detail_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')
    categories = Category.objects.filter(user=request.user)
    accounts = Account.objects.filter(user=request.user)
    currencies = Currency.objects.all()

    # Serialize transactions and categories for JSON
    transactions_data = [
        {
            'id': t.id,
            'date': t.date.strftime('%Y-%m-%d'),
            'category': t.category.name,
            'amount': str(t.amount),
            'description': t.description,
            'transaction_type': t.transaction_type,
            'currency': t.currency.currency_code,
            'account_name': t.account.account_name,
            'is_saved': t.is_saved
        } for t in transactions
    ]

    income_categories = []
    expense_categories = []
    
    for cat in categories.filter(is_income=True).annotate(
        transaction_count=Count('transaction'),
        total_amount=Sum('transaction__amount')
    ):
        income_categories.append({
            'id': cat.id,
            'name': cat.name,
            'transaction_count': cat.transaction_count or 0,
            'total_amount': str(cat.total_amount) if cat.total_amount else "0.00"
        })
    
    for cat in categories.filter(is_income=False).annotate(
        transaction_count=Count('transaction'),
        total_amount=Sum('transaction__amount')
    ):
        expense_categories.append({
            'id': cat.id,
            'name': cat.name,
            'transaction_count': cat.transaction_count or 0,
            'total_amount': str(cat.total_amount) if cat.total_amount else "0.00"
        })
    
    categories_data = {
        'true': income_categories,
        'false': expense_categories 
    }
    
    # 序列化帳戶數據
    accounts_data = [
        {
            'id': a.id,
            'account_name': a.account_name,
            'account_type': a.account_type,
            'balance': str(a.balance)
        } for a in accounts
    ]
    
    # 序列化貨幣數據
    currencies_data = [
        {
            'id': c.id,
            'currency_code': c.currency_code,
            'exchange_rate': str(c.exchange_rate)
        } for c in currencies
    ]

    return render(request, 'detail.html', {
        'transactions': transactions_data,
        'categories_json': categories_data,
        'accounts_json': accounts_data,
        'currencies_json': currencies_data
    })

@csrf_exempt
@require_POST
def add_transaction_view(request):
    try:
        date = request.POST.get('date')
        category_name = request.POST.get('category')
        transaction_type = request.POST.get('transaction_type') == 'true'
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        currency_code = request.POST.get('currency')
        account_name = request.POST.get('account')

        # Verify required fields
        if not date or not category_name or not amount or not account_name:
            return JsonResponse({'status': 'error', 'message': 'Date, category, amount and account are required'}, status=400)

        category, _ = Category.objects.get_or_create(name=category_name)

        account_obj, _ = Account.objects.get_or_create(
            user=request.user,
            account_name=account_name,
            defaults={'balance': '0.00'}
        )

        currency, _ = Currency.objects.get_or_create(
            currency_code=currency_code,
            defaults={'exchange_rate': '1.00'}
        )

        transaction = Transaction.objects.create(
            user=request.user,
            account=account_obj,
            date=date,
            category=category,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            currency=currency
        )

        return JsonResponse({'status': 'success', 'transaction_id': transaction.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def delete_transaction_view(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        transaction_id = request.POST.get('transaction_id')

        if not transaction_id:
            return JsonResponse({'status': 'error', 'message': 'Transaction ID is required'}, status=400)

        Transaction.objects.get(id=transaction_id).delete()

        import logging
        logger = logging.getLogger(__name__)
        logger.info('Transaction deleted')

        return JsonResponse({'status': 'success'})
    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
@require_POST
def update_transaction_view(request):
    try:
        transaction_id = request.POST.get('id')
        if not transaction_id:
            return JsonResponse({'status': 'error', 'message': 'Transaction ID required'}, status=400)

        transaction = Transaction.objects.get(id=transaction_id)

        # Get POST data
        date = request.POST.get('date')
        category_name = request.POST.get('category')
        transaction_type = request.POST.get('transaction_type') == 'true'
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        currency_code = request.POST.get('currency')
        account_name = request.POST.get('account')

        # Handle category
        if category_name:
            category, _ = Category.objects.get_or_create(name=category_name)
            transaction.category = category

        # Handle currency (ForeignKey)
        if currency_code:
            currency, _ = Currency.objects.get_or_create(
                currency_code=currency_code,
                defaults={'exchange_rate': '1.00'}
            )
            transaction.currency = currency

        # Handle account
        if account_name:
            account_obj, _ = Account.objects.get_or_create(
                user=request.user,
                account_name=account_name,
                defaults={'balance': '0.00'}
            )
            transaction.account = account_obj

        # Update other fields
        if date:
            transaction.date = date
        transaction.transaction_type = transaction_type
        if amount:
            transaction.amount = amount
        if description:
            transaction.description = description

        transaction.save()

        return JsonResponse({'status': 'success', 'transaction_id': transaction.id})

    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
def toggle_save_transaction(request):
    try:
        transaction_id = request.POST.get('transaction_id')
        
        if not transaction_id:
            return JsonResponse({'status': 'error', 'message': 'Transaction ID is required'}, status=400)
            
        transaction = Transaction.objects.get(id=transaction_id)
        
        transaction.is_saved = not transaction.is_saved
        transaction.save()
        
        return JsonResponse({
            'status': 'success', 
            'is_saved': transaction.is_saved,
            'message': 'Transaction saved status updated'
        })
        
    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
     
@login_required
def statistics_view(request):
    return render(request, 'statistics.html', {})

def get_transaction_dates(request):
    # Get Year and Month from Transactions
    transactions = Transaction.objects.all()
    
    months_by_year = {}
    years = set()
    
    for transaction in transactions:
        year = transaction.date.year
        month = transaction.date.month
        years.add(year)
        
        if year not in months_by_year:
            months_by_year[year] = set()
        months_by_year[year].add(month)
    
    years_list = sorted(list(years), reverse=True)
    months_by_year = {
        year: sorted(list(months)) 
        for year, months in months_by_year.items()
    }
    
    return JsonResponse({
        'years': years_list,
        'monthsByYear': months_by_year
    })

def get_statistics_data(request):
    try:
        year = request.GET.get('year')
        month = request.GET.get('month')
        mode = request.GET.get('mode', 'year')

        # initialize data structure
        monthly_data = {str(i): {'income': 0, 'expense': 0} for i in range(1, 13)}
        daily_data = {}
        expense_by_category = {}
        income_by_category = {}
        category_budgets = {}
        total_income = 0
        total_expense = 0
        total_budget = 0

        try:
            base_query = Transaction.objects.filter(date__year=year)
        except Exception:
            base_query = Transaction.objects.none()

        # handle monthly view
        if mode == 'month' and month:
            year_int = int(year)
            month_int = int(month)
            days_in_month = calendar.monthrange(year_int, month_int)[1]
            daily_data = {str(i): {'income': 0, 'expense': 0} for i in range(1, days_in_month + 1)}
            transactions = base_query.filter(date__month=month_int)
            # handle budget data
            budgets = Budget.objects.filter(
                period__year=int(year),
                period__month=int(month)
            )
            total_budget = sum(float(b.budget_amount) for b in budgets)
        else:
            transactions = base_query
            # handle budget data
            budgets = Budget.objects.filter(period__year=int(year))
            total_budget = sum(float(b.budget_amount) for b in budgets)

        # handle transactions
        for transaction in transactions:
            try:
                amount = abs(float(transaction.amount))
                month_num = str(transaction.date.month)
                day_num = str(transaction.date.day)
                category = transaction.category.name if transaction.category else 'Uncategorized'

                if transaction.transaction_type:  # Income
                    monthly_data[month_num]['income'] += amount
                    total_income += amount
                    income_by_category[category] = income_by_category.get(category, 0) + amount
                    
                    if mode == 'month' and month and day_num in daily_data:
                        daily_data[day_num]['income'] += amount
                else:  # Expense
                    monthly_data[month_num]['expense'] += amount
                    total_expense += amount
                    expense_by_category[category] = expense_by_category.get(category, 0) + amount
                    
                    # handle daily expense data
                    if mode == 'month' and month and day_num in daily_data:
                        daily_data[day_num]['expense'] += amount
            except Exception:
                continue

        # handle category budgets
        for budget in budgets:
            category_name = budget.category.name
            category_budgets[category_name] = category_budgets.get(category_name, 0) + float(budget.budget_amount)

        response_data = {
            'income': float(total_income),
            'expense': float(total_expense),
            'balance': float(total_income - total_expense),
            'monthly_data': monthly_data,
            'expense_by_category': expense_by_category,
            'income_by_category': income_by_category,
            'budget_data': {
                'total_budget': total_budget,
                'used_budget': float(total_expense),
                'category_budgets': category_budgets
            }
        }

        if mode == 'month' and month:
            response_data['daily_data'] = daily_data

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def management_view(request):
    # 獲取所有類別對象並計算交易數量和金額總和
    categories = Category.objects.filter(user=request.user).annotate(
        transaction_count=Count('transaction'),
        total_amount=Sum('transaction__amount')
    )

    income_categories = categories.filter(is_income=True)
    expense_categories = categories.filter(is_income=False)
    
    # 處理 Decimal 序列化
    income_categories_list = []
    for cat in income_categories:
        cat_dict = {
            'id': cat.id,
            'name': cat.name,
            'transaction_count': cat.transaction_count or 0,
            'total_amount': str(cat.total_amount) if cat.total_amount else "0.00"
        }
        income_categories_list.append(cat_dict)
    
    expense_categories_list = []
    for cat in expense_categories:
        cat_dict = {
            'id': cat.id,
            'name': cat.name,
            'transaction_count': cat.transaction_count or 0,
            'total_amount': f"{cat.total_amount:.2f}" if cat.total_amount else "0.00"
        }
        expense_categories_list.append(cat_dict)
    
    categories_data = {
        'true': income_categories_list,
        'false': expense_categories_list
    }

    accounts = Account.objects.filter(user=request.user)

    accounts_data = [
        {
            'id': a.id,
            'account_name': a.account_name,
            'account_type': a.account_type,
            'balance': str(a.balance)
        } for a in accounts
    ]
    
    return render(request, 'management.html', {
        # 'income_categories': income_categories,
        # 'expense_categories': expense_categories,
        'categories_json': json.dumps(categories_data),
        # 'income_categories_list': json.dumps(income_categories_list),
        # 'expense_categories_list': json.dumps(expense_categories_list)
        'accounts_json': accounts_data,
    })

@csrf_exempt
@require_POST
def add_category(request):
    category_name = request.POST.get('name')
    is_income = request.POST.get('is_income') == 'true'

    if not category_name:
        return JsonResponse({'status': 'error', 'message': 'Category name is required'}, status=400)

    category, created = Category.objects.get_or_create(
        name=category_name,
        defaults={'is_income': is_income}
    )

    if not created:
        return JsonResponse({'status': 'exists', 'message': 'Category already exists'})

    return JsonResponse({'status': 'success', 'id': category.id, 'name': category.name})

@csrf_exempt
def delete_category_view(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        category_id = request.POST.get('category_id')

        if not category_id:
            return JsonResponse({'status': 'error', 'message': 'Category ID is required'}, status=400)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
        
        # 檢查是否有交易使用此類別
        if category.transaction_set.exists():
            return JsonResponse({
                'status': 'error', 
                'message': '無法刪除：有交易使用此類別。請先刪除或重新分類這些交易。'
            }, status=400)
        
        # 刪除類別
        category.delete()

        return JsonResponse({'status': 'success', 'message': '類別已成功刪除'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@csrf_exempt
@require_POST
def add_budget_view(request):
    try:
        period = request.POST.get('period')
        category_id = request.POST.get('category_id')
        budget_amount = request.POST.get('budget_amount')
        
        if not period or not category_id or not budget_amount:
            return JsonResponse({'status': 'error', 'message': 'All fields are required'}, status=400)
        
        # Convert year and month strings to date objects (using the first day of the month)
        from datetime import datetime
        period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
        
        category = Category.objects.get(id=category_id)
        
        budget, created = Budget.objects.update_or_create(
            user=request.user,
            category=category,
            period=period_date,
            defaults={'budget_amount': budget_amount}
        )
        
        return JsonResponse({
            'status': 'success', 
            'id': budget.id,
            'message': 'Budget added successfully'
        })
        
    except Category.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@csrf_exempt
@require_POST
def update_budget_view(request):
    try:
        budget_id = request.POST.get('budget_id')
        period = request.POST.get('period')
        category_id = request.POST.get('category_id')
        budget_amount = request.POST.get('budget_amount')
        
        if not budget_id:
            return JsonResponse({'status': 'error', 'message': 'Budget ID is required'}, status=400)
            
        budget = Budget.objects.get(id=budget_id, user=request.user)
        
        if period:
            from datetime import datetime
            period_date = datetime.strptime(period + "-01", "%Y-%m-%d").date()
            budget.period = period_date
            
        if category_id:
            category = Category.objects.get(id=category_id)
            budget.category = category
            
        if budget_amount:
            budget.budget_amount = budget_amount
            
        budget.save()
        
        return JsonResponse({'status': 'success', 'message': 'Budget updated successfully'})
        
    except Budget.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Budget not found'}, status=404)
    except Category.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@csrf_exempt
def delete_budget_view(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        budget_id = request.POST.get('budget_id')
        
        if not budget_id:
            return JsonResponse({'status': 'error', 'message': 'Budget ID is required'}, status=400)
            
        budget = Budget.objects.get(id=budget_id, user=request.user)
        budget.delete()
        
        return JsonResponse({'status': 'success', 'message': 'Budget deleted successfully'})
        
    except Budget.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def get_budgets_view(request):
    try:
        # 獲取當前用戶的所有預算
        budgets = Budget.objects.filter(user=request.user)
        
        # 序列化預算數據
        budget_list = []
        for budget in budgets:
            # 計算剩餘金額
            # 獲取與該預算相同月份和類別的交易
            from django.db.models import Sum
            from datetime import datetime
            
            year = budget.period.year
            month = budget.period.month
            
            # 獲取該月的支出總額
            spent_amount = Transaction.objects.filter(
                user=request.user,
                category=budget.category,
                date__year=year,
                date__month=month,
                transaction_type=False  # 僅支出交易
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            # 計算剩餘金額
            remaining_amount = budget.budget_amount - spent_amount
            
            # 添加預算信息
            budget_dict = {
                'id': budget.id,
                'period': budget.period.strftime('%Y-%m'),
                'category_id': budget.category.id,
                'category_name': budget.category.name,
                'budget_amount': str(budget.budget_amount),
                'remaining_amount': str(remaining_amount)
            }
            budget_list.append(budget_dict)
            
        return JsonResponse({'status': 'success', 'budgets': budget_list})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'獲取預算時發生錯誤: {str(e)}'}, status=500)

@csrf_exempt
def add_currency_view(request):
    if request.method == 'POST':
        currency_code = request.POST.get('currency_code')
        # exchange_rate = request.POST.get('exchange_rate')
        
        try:
            currency = Currency.objects.create(
                currency_code=currency_code,
                # exchange_rate=exchange_rate
            )
            return JsonResponse({'status': 'success', 'message': 'Currency added successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Add currency failed: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_currency_view(request):
    if request.method == 'POST':
        currency_id = request.POST.get('currency_id')
        
        try:
            currency = Currency.objects.get(id=currency_id)
            currency.delete()
            return JsonResponse({'status': 'success', 'message': 'Currency deleted successfully'})
        except Currency.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Currency not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Delete currency failed: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def add_account_view(request):
    if request.method == 'POST':
        account_name = request.POST.get('account_name')
        account_type = request.POST.get('account_type')
        balance = request.POST.get('balance')
        
        try:
            account = Account.objects.create(
                user=request.user,
                account_name=account_name,
                account_type=account_type,
                balance=balance,
            )
            return JsonResponse({'status': 'success', 'message': 'Account added successfully', 'account': {
                'id': account.id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'balance': str(account.balance)
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Add account failed: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def delete_account_view(request):
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        
        if not account_id:
            return JsonResponse({'status': 'error', 'message': 'Account ID is required'}, status=400)
        
        try:
            account = Account.objects.get(id=account_id)
            account.delete()
            return JsonResponse({'status': 'success', 'message': 'Account deleted successfully'})
        except Account.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Account not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Delete account failed: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
@login_required
def get_accounts_view(request):
    try:
        print(f"User: {request.user.username}, Finding accounts...")
        
        accounts = Account.objects.filter(user=request.user)
        print(f"Found {accounts.count()} accounts")
        
        account_list = []
        for account in accounts:
            account_dict = {
                'id': account.id,
                'account_name': account.account_name,
                'account_type': account.account_type,
                'balance': str(account.balance)
            }
            account_list.append(account_dict)
            
        print(f"Returning {len(account_list)} accounts")
        return JsonResponse({'status': 'success', 'accounts': account_list})
    except Exception as e:
        print(f"Error in get_accounts_view: {str(e)}")
        return JsonResponse({'status': 'error', 'message': f'Get accounts failed: {str(e)}'}, status=500)


def get_transaction_dates(request):
    # Get Year and Month from Transactions
    transactions = Transaction.objects.filter(user=request.user)
    
    months_by_year = {}
    years = set()
    
    for transaction in transactions:
        year = transaction.date.year
        month = transaction.date.month
        years.add(year)
        
        if year not in months_by_year:
            months_by_year[year] = set()
        months_by_year[year].add(month)
    
    years_list = sorted(list(years), reverse=True)
    months_by_year = {
        year: sorted(list(months)) 
        for year, months in months_by_year.items()
    }
    
    return JsonResponse({
        'years': years_list,
        'monthsByYear': months_by_year
    })

def get_statistics_data(request):
    try:
        year = request.GET.get('year')
        month = request.GET.get('month')
        mode = request.GET.get('mode', 'year')

        print(f"Debug - Received request params: year={year}, month={month}, mode={mode}")

        if year:
            year_transactions = Transaction.objects.filter(date__year=year)
        else:
            year_transactions = Transaction.objects.all()
            
        monthly_data = {}
        for i in range(1, 13):
            monthly_data[i] = {
                'income': 0,
                'expense': 0
            }

        expense_by_category = {}
        income_by_category = {}


        # calculate data based on selected month or year
        if mode == 'month' and month:
            transactions = year_transactions.filter(date__month=month)
        else:
            transactions = year_transactions

        total_income = 0
        total_expense = 0

        # deal with transaction records
        for transaction in transactions:
            try:
                month_num = transaction.date.month
                amount = abs(float(transaction.amount))
                category = transaction.category.name
                                
                if transaction.transaction_type:  # Income
                    monthly_data[month_num]['income'] += amount
                    total_income += amount
                    income_by_category[category] = income_by_category.get(category, 0) + amount
                else:  # Expense
                    monthly_data[month_num]['expense'] += amount
                    total_expense += amount
                    expense_by_category[category] = expense_by_category.get(category, 0) + amount
                
            except Exception as e:
                print(f"Error processing transaction: {str(e)}")
                continue

        response_data = {
            'income': float(total_income),
            'expense': float(total_expense),
            'balance': float(total_income - total_expense),
            'monthly_data': monthly_data,
            'expense_by_category': expense_by_category,
            'income_by_category': income_by_category
        }

        print(f"Debug - Sending response: {response_data}")
        return JsonResponse(response_data)

    except Exception as e:
        print(f"Error in get_statistics_data: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': str(e),
            'detail': traceback.format_exc()
        }, status=500)
    
@login_required
def user_instruction(request):
    return render(request, 'user_instruction.html')

@login_required
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Here you can add code to handle the form submission
        # For example, send an email or save to database
        
        messages.success(request, 'Thank you for your message. We will get back to you soon!')
        return redirect('contact')
        
    return render(request, 'contact.html')