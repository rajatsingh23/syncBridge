from django.conf import settings
from django.shortcuts import redirect
from django.views import View

from integrations.providers.shopify_oauth import ShopifyOAuth
from django.http import HttpResponseBadRequest, HttpResponse


class ShopifyOAuthStartView(View):
    def get(self, request):
        shop_domain = request.GET.get("shop")

        if not shop_domain or not shop_domain.endswith(".myshopify.com"):
            return HttpResponseBadRequest("Invalid Shopify shop domain.")
        oauth = ShopifyOAuth(
            client_id=settings.SHOPIFY_CLIENT_ID,
            redirect_uri=settings.SHOPIFY_REDIRECT_URI,
            scopes=settings.SHOPIFY_SCOPES,
        )

        state = oauth.generate_state()

        request.session["shopify_oauth_state"] = state

        authorization_url = oauth.build_authorization_url(
            shop_domain=request.GET["shop"],
            state=state,
        )

        return redirect(authorization_url)

class ShopifyOAuthCallbackView(View):
    def get(self, request):
        expected_state = request.session.get("shopify_oauth_state")
        received_state = request.GET.get("state")

        if not expected_state or not received_state:
            return HttpResponseBadRequest("Invalid OAuth state.")

        oauth = ShopifyOAuth(
            client_id=settings.SHOPIFY_CLIENT_ID,
            redirect_uri=settings.SHOPIFY_REDIRECT_URI,
            scopes=settings.SHOPIFY_SCOPES,
        )

        if not oauth.validate_state(expected_state, received_state):
            return HttpResponseBadRequest("Invalid OAuth state.")

        return HttpResponse("OAuth state validated.")