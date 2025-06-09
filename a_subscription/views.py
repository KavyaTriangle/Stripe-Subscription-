from django.shortcuts import render, reverse, redirect, get_object_or_404

import stripe
from datetime import datetime
from .models import *

from django.conf import settings
stripe.api_key = settings.STRIPE_SECRET_KEY


# def subscription_view(request):
#     subscription = {
#         'basic': 'price_1RT4BxQcQYGpykCiplcKii3h',
#         'pro': 'price_1RT4EvQcQYGpykCiWtzyQ2NA',
#         'premium': 'price_1RT4FHQcQYGpykCiCA7UyhNo',
#     }

#     if request.method == 'POST':
#         if not request.user.is_authenticated:
#             return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next = {request.get_full_path()}')

#         price_id = request.POST.get("price_id")
#         subscription = Subscription.objects.filter(user=request.user).first()
#         if subscription:
#             stripe_subscription = stripe.Subscription.retrieve(subscription.subscription_id)
#             item = stripe_subscription['items']['data'][0]
#             stripe.Subscription.modify(
#                 subscription.subscription_id,
#                 items = [{
#                     'id': item['id'],
#                     'price': price_id,
#                 }],
#                 cancel_at_period_end = False
#             )
#             price = stripe.Price.retrieve(price_id)
#             product = stripe.Product.retrieve(price['product'])

#             subscription.startdate = now()
#             subscription.product_name = product.name
#             subscription.price = price['unit_amount']/100
#             subscription.end_date = None
#             subscription.canceled_at=None 
#             Subscription.save()
#             return redirect('my_sub') 
#         else:   
#             checkout_session = stripe.checkout.Session.create(
#                 line_items=[
#                     {
#                         'price': price_id,
#                         'quantity': 1,
#                     },
#                 ],

#                 payment_method_types=['card'],
#                 mode='subscription',
#                 success_url=request.build_absolute_uri(
#                     reverse('create_subscription'))+f'?session_id={{CHECKOUT_SESSION_ID}}',
#                 cancel_url=request.build_absolute_uri(
#                     f'{reverse('subscription')}'),
#                 customer_email=request.user.email,
#                 metadata={
#                     'user_id': request.user.id,
#                 }
#             )
#             return redirect(checkout_session.url, code=303)

#     return render(request, 'a_subscription/subscription.html', {'subscription': subscription})

def subscription_view(request):
    subscription_prices = {
        'basic': 'price_1RT4BxQcQYGpykCiplcKii3h',
        'pro': 'price_1RT4EvQcQYGpykCiWtzyQ2NA',
        'premium': 'price_1RT4FHQcQYGpykCiCA7UyhNo',
    }

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next={request.get_full_path()}')

        price_id = request.POST.get("price_id")
        if not price_id:
            return HttpResponseBadRequest("Price ID is required.")

        user_subscription = Subscription.objects.filter(user=request.user).first()
        if user_subscription:
            stripe_subscription = stripe.Subscription.retrieve(user_subscription.subscription_id)
            item = stripe_subscription['items']['data'][0]
            stripe.Subscription.modify(
                user_subscription.subscription_id,
                items=[{
                    'id': item['id'],
                    'price': price_id,
                }],
                cancel_at_period_end=False
            )
            price = stripe.Price.retrieve(price_id)
            product = stripe.Product.retrieve(price['product'])

            user_subscription.startdate = now()
            user_subscription.product_name = product.name
            user_subscription.price = price['unit_amount'] / 100
            user_subscription.end_date = None
            user_subscription.canceled_at = None
            user_subscription.save()

            return redirect('my_sub')
        else:
            checkout_session = stripe.checkout.Session.create(
                line_items=[{'price': price_id, 'quantity': 1}],
                payment_method_types=['card'],
                mode='subscription',
                success_url=request.build_absolute_uri(
                    reverse('create_subscription')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('subscription')),
                customer_email=request.user.email,
                metadata={'user_id': request.user.id}
            )
            return redirect(checkout_session.url, code=303)

    return render(request, 'a_subscription/subscription.html', {'subscription': subscription_prices})


def create_subscription(request):
    checkout_session_id = request.GET.get('session_id', None)
    session = stripe.checkout.Session.retrieve(checkout_session_id)

    user_id = session.metadata.get("user_id")
    user = User.objects.get(id=user_id)

    subscription = stripe.Subscription.retrieve(session.subscription)
    price = subscription['items']['data'][0]['price']
    product_id = price['product']
    product = stripe.Product.retrieve(product_id)

    # Try to get current_period_start safely
    current_period_start = subscription.get('current_period_start')

    if current_period_start:
        start_date = datetime.fromtimestamp(current_period_start)
    else:
        # fallback if current_period_start is not yet available
        print("WARNING: current_period_start is missing. Using now() as fallback.")
        start_date = now()

    if checkout_session_id:
        Subscription.objects.create(
            user=user,
            customer_id=session.customer,
            subscription_id=session.subscription,
            product_name=product.name,
            price=price['unit_amount'] / 100,
            interval=price['recurring']['interval'],
            start_date=start_date,
        )

    return redirect('my_sub')



def my_sub_view(request):
    if not request.user.is_authenticated:
        return redirect('account_login')
    subscription = Subscription.objects.filter(user=request.user).first()

    return render(request, 'a_subscription/my-sub.html', {'subscription': subscription})



