from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from rich import _console
from finance.forms import TransactionForm
from finance.models import User, Category, Transaction
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
    transactions = Transaction.objects.all().order_by('date')
    categories = Category.objects.all()

    # Serialize transactions and categories for JSON
    transactions_data = [
        {
            'date': t.date.strftime('%Y-%m-%d'),
            'category': t.category,
            'amount': str(t.amount),
            'description': t.description,
            'transaction_type': "Income" if t.transaction_type else "Expenditure",
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