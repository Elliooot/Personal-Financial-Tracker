import requests
from decimal import Decimal
from django.conf import settings
import logging
import json
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from finance.currency_utils import get_exchange_rate_with_gbp_base
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum
from finance.forms import CategoryForm, TransactionForm
from finance.models import User, Account, Category, Transaction, Currency, Budget
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
import traceback
import calendar

logger = logging.getLogger(__name__)

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

        category, _ = Category.objects.get_or_create(name=category_name, user=request.user)

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
    transactions = Transaction.objects.filter(user=request.user)
    # transactions = Transaction.objects.all()
    
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
    transactions = Transaction.objects.filter(user=request.user)

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
            base_query = transactions.filter(date__year=year)
        except Exception:
            base_query = transactions.none()

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

    currencies = Currency.objects.filter(Q(user=None) | Q(user=request.user))
    
    currencies_data = [
        {
            'id': c.id,
            'currency_code': c.currency_code,
            'exchange_rate': str(c.exchange_rate),
            'is_system': c.user is None
        } for c in currencies
    ]

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
        'currencies_json': currencies_data,
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
        user=request.user,
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
    
@login_required
def get_currencies_view(request):
    try:
        system_currencies = Currency.objects.filter(user=None)
        user_currencies = Currency.objects.filter(user=request.user)
        
        currencies_list = []
        
        for currency in system_currencies:
            currencies_list.append({
                'id': currency.id,
                'currency_code': currency.currency_code,
                'exchange_rate': float(currency.exchange_rate),
                'last_updated': currency.last_updated.isoformat(),
                'is_system': True
            })
        
        for currency in user_currencies:
            currencies_list.append({
                'id': currency.id,
                'currency_code': currency.currency_code,
                'exchange_rate': float(currency.exchange_rate),
                'last_updated': currency.last_updated.isoformat(),
                'is_system': False
            })
        
        return JsonResponse({
            'status': 'success',
            'currencies': currencies_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def get_available_currencies_view(request):
    try:
        system_currencies = Currency.objects.filter(user=None)
        user_currencies = Currency.objects.filter(user=request.user)
        
        currencies_list = []
        
        for currency in list(system_currencies):
            currencies_list.append({
                'id': currency.id,
                'currency_code': currency.currency_code,
                'exchange_rate': float(currency.exchange_rate),
                'user': None
            })
        
        for currency in list(user_currencies):
            currencies_list.append({
                'id': currency.id,
                'currency_code': currency.currency_code,
                'exchange_rate': float(currency.exchange_rate),
                'user': request.user.id
            })
        
        return JsonResponse({
            'status': 'success',
            'currencies': currencies_list
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@csrf_exempt
@login_required
def add_currency_view(request):
    from finance.currency_utils import get_exchange_rate_with_gbp_base
    if request.method == 'POST':
        currency_code = request.POST.get('currency_code')
        
        if not currency_code:
            return JsonResponse({'status': 'error', 'message': 'Currency code is required'}, status=400)
        
        try:
            # Check if currency already exists
            if Currency.objects.filter(currency_code=currency_code).exists():
                return JsonResponse({'status': 'exists', 'message': 'Currency already exists'})
            
            # Get exchange rate using GBP as base currency
            try:
                exchange_rate = get_exchange_rate_with_gbp_base(currency_code)
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'Failed to fetch exchange rate: {str(e)}'
                }, status=500)
            
            # Create new currency
            currency = Currency.objects.create(
                user=request.user,  # Associate with current user
                currency_code=currency_code,
                exchange_rate=exchange_rate
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Currency added successfully',
                'currency': {
                    'id': currency.id,
                    'currency_code': currency.currency_code,
                    'exchange_rate': float(currency.exchange_rate),
                    'last_updated': currency.last_updated.isoformat()
                }
            })
        
        except Exception as e:
            logger.error(f"Error adding currency: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Add currency failed: {str(e)}'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required
def refresh_exchange_rates_view(request):
    """
    View to refresh exchange rates for the current user's currencies.
    """
    from finance.currency_utils import get_multiple_rates_with_gbp_base
    try:
        # Get all currencies for this user
        currencies = Currency.objects.filter(user=request.user)
        currency_codes = [c.currency_code for c in currencies]
        
        if not currency_codes:
            return JsonResponse({
                'status': 'info',
                'message': 'No currencies to update'
            })
        
        # Get all exchange rates at once to minimize API calls
        try:
            rates = get_multiple_rates_with_gbp_base(currency_codes)
        except Exception as e:
            logger.error(f"Failed to get exchange rates: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to get exchange rates: {str(e)}'
            }, status=500)
        
        # Update each currency with new rates
        updated_count = 0
        updated_currencies = {}
        
        for currency in currencies:
            code = currency.currency_code
            if code in rates:
                old_rate = currency.exchange_rate
                currency.exchange_rate = rates[code]
                currency.save()
                updated_count += 1
                updated_currencies[code] = {
                    'old_rate': float(old_rate),
                    'new_rate': float(rates[code])
                }
                
        return JsonResponse({
            'status': 'success',
            'message': f'Updated {updated_count} currencies',
            'updated_count': updated_count,
            'updated_currencies': updated_currencies
        })
            
    except Exception as e:
        logger.error(f"Error refreshing exchange rates: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to update exchange rates: {str(e)}'
        }, status=500)

def get_exchange_rate_with_gbp_base(currency_code):
    """
    Calculate exchange rate with GBP as base currency using Open Exchange Rates API.
    
    This function works with the free tier of Open Exchange Rates by:
    1. Getting USD rates for both GBP and the target currency
    2. Calculating the cross rate between them
    
    Args:
        currency_code (str): Target currency code (e.g., 'EUR', 'JPY')
        
    Returns:
        Decimal: Exchange rate as GBP to target currency
    """
    API_KEY = settings.OPENEXCHANGERATES_API_KEY
    
    # If the target is GBP, return 1.0
    if currency_code == 'GBP':
        return Decimal('1.0')
    
    try:
        # We need both GBP and the target currency rates against USD
        url = "https://openexchangerates.org/api/latest.json"
        params = {
            'app_id': API_KEY,
            'base': 'USD',  # Free tier only supports USD as base
            'symbols': f"GBP,{currency_code}"  # Get both GBP and target rates
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data:
            logger.error(f"Invalid API response: {data}")
            raise Exception("Invalid API response: 'rates' field missing")
        
        # Extract rates
        if 'GBP' not in data['rates'] or currency_code not in data['rates']:
            missing = []
            if 'GBP' not in data['rates']:
                missing.append('GBP')
            if currency_code not in data['rates']:
                missing.append(currency_code)
            raise Exception(f"Currency rates not found in response: {', '.join(missing)}")
        
        # Get USD to GBP and USD to target rates
        usd_to_gbp = Decimal(str(data['rates']['GBP']))
        usd_to_target = Decimal(str(data['rates'][currency_code]))
        
        # Calculate GBP to target rate:
        # GBP to target = (USD to target) / (USD to GBP)
        gbp_to_target = usd_to_target / usd_to_gbp
        
        logger.info(f"Calculated GBP to {currency_code} rate: {gbp_to_target}")
        return gbp_to_target
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise Exception(f"Failed to fetch exchange rate: {str(e)}")
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        raise Exception(f"Failed to parse exchange rate data: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception(f"Failed to get exchange rate: {str(e)}")


def get_multiple_rates_with_gbp_base(currency_codes):
    """
    Get multiple exchange rates with GBP as base currency in a single API call.
    
    Args:
        currency_codes (list): List of currency codes to get rates for
        
    Returns:
        dict: Dictionary of currency codes to exchange rates (GBP as base)
    """
    API_KEY = settings.OPENEXCHANGERATES_API_KEY
    
    # Filter out GBP if it's in the list (it would always be 1.0)
    codes_to_fetch = [code for code in currency_codes if code != 'GBP']
    
    # If only GBP was requested, return immediately
    if not codes_to_fetch:
        return {'GBP': Decimal('1.0')}
    
    # Add GBP to the list of currencies to fetch
    if 'GBP' not in codes_to_fetch:
        codes_to_fetch.append('GBP')
    
    try:
        # Prepare API call
        url = "https://openexchangerates.org/api/latest.json"
        params = {
            'app_id': API_KEY,
            'base': 'USD',
            'symbols': ','.join(codes_to_fetch)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data or 'GBP' not in data['rates']:
            logger.error(f"Invalid API response or GBP rate missing: {data}")
            raise Exception("Invalid API response: required rates missing")
        
        # Get the USD to GBP rate
        usd_to_gbp = Decimal(str(data['rates']['GBP']))
        
        # Calculate all rates with GBP as base
        result = {'GBP': Decimal('1.0')}  # GBP to GBP is always 1.0
        
        for code in currency_codes:
            if code == 'GBP':
                continue  # Already added
                
            if code in data['rates']:
                # Convert: GBP to target = (USD to target) / (USD to GBP)
                usd_to_target = Decimal(str(data['rates'][code]))
                gbp_to_target = usd_to_target / usd_to_gbp
                result[code] = gbp_to_target
            else:
                logger.warning(f"Currency {code} not found in API response")
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching multiple exchange rates: {str(e)}")
        raise Exception(f"Failed to fetch exchange rates: {str(e)}")


def update_all_currency_rates_gbp_base():
    """
    Update all currency exchange rates in the database using GBP as base currency.
    """
    from finance.models import Currency  # Import here to avoid circular imports
    
    try:
        # Get all currencies from database
        currencies = Currency.objects.all()
        currency_codes = [c.currency_code for c in currencies]
        
        if not currency_codes:
            logger.info("No currencies to update")
            return {"status": "success", "message": "No currencies to update"}
        
        # Fetch all rates at once with GBP as base
        rates = get_multiple_rates_with_gbp_base(currency_codes)
        
        # Update each currency
        updated = 0
        for currency in currencies:
            code = currency.currency_code
            
            if code in rates:
                currency.exchange_rate = rates[code]
                currency.save()
                updated += 1
                logger.debug(f"Updated {code} rate to {rates[code]}")
            else:
                logger.warning(f"Could not update rate for {code}")
        
        logger.info(f"Updated {updated} of {len(currencies)} currencies with GBP as base")
        
        return {
            "status": "success", 
            "message": f"Updated {updated} currencies with GBP as base",
            "updated_count": updated,
            "total_count": len(currencies)
        }
        
    except Exception as e:
        error_msg = f"Failed to update currency rates: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

class Command(BaseCommand):
    help = 'Add default currencies for existing users'

    def handle(self, *args, **options):
        users = User.objects.all()
        self.stdout.write(f"Found {users.count()} users")
        
        default_currencies = ['GBP', 'EUR', 'USD']
        
        for user in users:
            self.stdout.write(f"Processing user: {user.username}")
            added_count = 0
            
            for currency_code in default_currencies:
                # Skip if user already has this currency
                if Currency.objects.filter(user=user, currency_code=currency_code).exists():
                    self.stdout.write(f"  {currency_code} already exists for {user.username}")
                    continue
                
                try:
                    # Try to get exchange rate from API
                    try:
                        exchange_rate = get_exchange_rate_with_gbp_base(currency_code)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"  Failed to get exchange rate for {currency_code}: {str(e)}"
                        ))
                        # Fallback values
                        if currency_code == 'GBP':
                            exchange_rate = 1.0
                        elif currency_code == 'EUR':
                            exchange_rate = 1.19
                        elif currency_code == 'USD':
                            exchange_rate = 1.28
                        else:
                            exchange_rate = 1.0
                    
                    # Create the currency
                    Currency.objects.create(
                        user=user,
                        currency_code=currency_code,
                        exchange_rate=exchange_rate
                    )
                    added_count += 1
                    self.stdout.write(f"  Added {currency_code} for {user.username}")
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"  Error adding {currency_code} for {user.username}: {str(e)}"
                    ))
            
            self.stdout.write(f"Added {added_count} currencies for {user.username}")
            
        self.stdout.write(self.style.SUCCESS("Default currencies have been added to existing users"))

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
def get_available_currencies(request):
    system_currencies = Currency.objects.filter(user=None)
    user_currencies = Currency.objects.filter(user=request.user)
    all_currencies = list(system_currencies) + list(user_currencies)
    return all_currencies

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
    
@csrf_exempt
@login_required
def order_accounts_view(request): 
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            account_ids = data.get('account_ids', [])
            
            if not account_ids:
                return JsonResponse({'status': 'error', 'message': 'Account IDs are required'}, status=400)
            
            for order, account_id in enumerate(account_ids):
                Account.objects.filter(id=account_id, user=request.user).update(order=order)
            
            return JsonResponse({'status': 'success', 'message': 'Account orders updated successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Update account orders failed: {str(e)}'}, status=500)
    
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