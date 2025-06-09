from django.shortcuts import render, redirect, reverse
import stripe
from django.conf import settings
from .models import *
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

stripe.api_key = settings.STRIPE_SECRET_KEY


def product_view(request):
    product_id = 'prod_SNitB1Ba6BzXYU'
    product = stripe.Product.retrieve(product_id)
    prices = stripe.Price.list(product=product_id)
    price = prices.data[0]
    product_price = price.unit_amount / 100.0

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next = {request.get_full_path()}')

        price_id = request.POST.get("price_id")
        quantity = request.POST.get("quantity")

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {              
                'price':price_id,
                'quantity':quantity,
                }             
            ],
            payment_method_types = ['card'],
            mode = 'payment',
            customer_creation = 'always',
            success_url=f'{settings.BASE_URL}{reverse("payment_sucessfull")}?session_id={{CHECKOUT_SESSION_ID}}',

            cancel_url=f'{settings.BASE_URL}{reverse('payment_cancelled')}'
        )
        return redirect(checkout_session.url, code=303)

    return render(request, 'a_stripe/product.html', {'product': product, 'product_price': product_price})


def payment_sucessfull(request):
    checkout_session_id = request.GET.get('session_id',None)
    if checkout_session_id:
        session = stripe.checkout.Session.retrieve(checkout_session_id)
        customer_id = session.customer
        customer = stripe.Customer.retrieve(customer_id)

        line_item = stripe.checkout.Session.list_line_items(checkout_session_id).data[0]
        
        UserPayment.objects.get_or_create(
            user = request.user,
            stripe_customer_id = customer_id,
            stripe_checkout_id = checkout_session_id,
            stripe_product_id = line_item.price.product,
            product_name = line_item.description,
            quantity = line_item.quantity,
            price = line_item.price.unit_amount/100.0,
            currency = line_item.price.currency,
            has_paid = True
        )

    return render(request,'a_stripe/payment_sucessfull.html',{'customer': customer})

def payment_cancelled(request):
    return render(request,'a_stripe/payment_cancelled.html')


@require_POST # It is a decorator Execute only by post request
@csrf_exempt  # Stripe cannot handle CSRF tokens, so we exempt it
def stripe_webhook(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET,
    payload = request.body,
    sig_header = request.META['HTTP_STRIPE_SIGNATURE'],
    event=None,

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except :
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.Session.completed':
        session = event['data']['object']
        checkout_session_id = session.get('id')
        user_payment = UserPayment.objects.get(stripe_checkout_id = checkout_session_id)
        user_payment.has_paid = True
        user_payment.save()
    
    return HttpResponse(status=200)