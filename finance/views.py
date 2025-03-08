from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rich import _console
from finance.forms import TransactionForm
from django.db.models import Count, Sum
from finance.models import User, Category, Transaction
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
import traceback



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
    transactions = Transaction.objects.all().order_by('date')
    categories = Category.objects.all()

    # Serialize transactions and categories for JSON
    transactions_data = [
        {
            'date': t.date.strftime('%Y-%m-%d'),
            'category': t.get_category_display(),
            'amount': str(t.amount),
            'description': t.description,
            'transaction_type': "Income" if t.transaction_type else "Expense",
            'currency': t.currency.currency_code
        } for t in transactions
    ]

    return render(request, 'detail.html', {'transactions': transactions_data, })

@csrf_exempt
def delete_transaction_view(request):
    try:
        transaction_id = request.POST.get('transaction_id')
        Transaction.objects.get(id=transaction_id).delete()
        _console.log('Transaction deleted')
        return JsonResponse({'status': 'success'})
    except Transaction.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaction not found'}, status=404)

def statistics_view(request):
    # 可以根據需求計算統計數據，這裡只傳遞一個空 context 作為範例
    return render(request, 'statistics.html', {})

def management_view(request):
    # 傳遞管理頁面需要的資料
    categories = Category.objects.all()
    return render(request, 'management.html', {'categories': categories})

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
                category = transaction.get_category_display()
                                
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