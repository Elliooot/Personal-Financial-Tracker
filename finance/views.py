import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum
from rich import _console
from finance.forms import CategoryForm, TransactionForm
from finance.models import User, Account, Category, Transaction, Currency
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required


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
    transactions = Transaction.objects.all().order_by('-date')
    categories = Category.objects.all()

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
            'account': t.account.account_name
        } for t in transactions
    ]

    income_categories = [c.name for c in categories if c.is_income]
    expense_categories = [c.name for c in categories if not c.is_income]
    
    categories_data = {
        'true': income_categories,
        'false': expense_categories 
    }

    return render(request, 'detail.html', {
        'transactions': transactions_data, 
        'categories_json': categories_data,
        # 'categories': categories # Keep original categories for modal selection
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

    
def statistics_view(request):

    return render(request, 'statistics.html', {})

def management_view(request):
    # 獲取所有類別對象並計算交易數量和金額總和
    categories = Category.objects.all().annotate(
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
    
    return render(request, 'management.html', {
        # 'income_categories': income_categories,
        # 'expense_categories': expense_categories,
        'categories_json': json.dumps(categories_data),
        # 'income_categories_list': json.dumps(income_categories_list),
        # 'expense_categories_list': json.dumps(expense_categories_list)
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

    return JsonResponse({'status': 'success', 'name': category.name})

@csrf_exempt
def delete_category_view(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    
    try:
        category_id = request.POST.get('category_id')

        if not category_id:
            return JsonResponse({'status': 'error', 'message': 'Category ID is required'}, status=400)

        Category.objects.get(id=category_id).delete()

        import logging
        logger = logging.getLogger(__name__)
        logger.info('Category deleted')

        return JsonResponse({'status': 'success'})
    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)