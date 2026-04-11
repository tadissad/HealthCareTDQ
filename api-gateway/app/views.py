"""
views.py – api-gateway
========================
Cổng vào duy nhất của toàn bộ hệ thống health-micro-ai.
Xử lý: xác thực người dùng, proxy request đến các microservice nội bộ,
và render HTML templates cho Web UI.

Luồng xác thực:
  1. Người dùng đăng nhập → api-gateway kiểm tra Account local
  2. Nếu hợp lệ → gọi auth-service để lấy JWT token
  3. JWT được lưu trong session
  4. Mọi request nội bộ đến microservices đều kèm JWT header (X-Internal-Token)
"""
import hashlib
import logging
import requests
from functools import wraps

from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.contrib import messages

from .models import Account

logger = logging.getLogger(__name__)

# ── Healthcare Service URL shortcuts ──────────────────────────────────────────
AUTH_URL             = getattr(settings, 'AUTH_SERVICE_URL',              'http://auth-service:8000')
PATIENT_URL          = getattr(settings, 'PATIENT_SERVICE_URL',           'http://patient-service:8000')
PHARMACY_URL         = getattr(settings, 'PHARMACY_SERVICE_URL',          'http://pharmacy-service:8000')
MED_CATALOG_URL      = getattr(settings, 'MEDICAL_CATALOG_SERVICE_URL',   'http://medical-catalog-service:8000')
PRESCRIPTION_URL     = getattr(settings, 'PRESCRIPTION_SERVICE_URL',      'http://prescription-service:8000')
DISPENSING_URL       = getattr(settings, 'DISPENSING_SERVICE_URL',        'http://dispensing-service:8000')
MED_REVIEW_URL       = getattr(settings, 'MEDICAL_REVIEW_SERVICE_URL',    'http://medical-review-service:8000')
CLINICAL_ADV_URL     = getattr(settings, 'CLINICAL_ADVISORY_SERVICE_URL', 'http://clinical-advisory-service:8000')
TREATMENT_REC_URL    = getattr(settings, 'TREATMENT_REC_SERVICE_URL',     'http://treatment-recommender-service:8000')


# ── Helper Functions ──────────────────────────────────────────────────────────

def hash_password(raw_password: str) -> str:
    """SHA-256 hash. Production: dùng bcrypt."""
    return hashlib.sha256(raw_password.encode()).hexdigest()


def _get_jwt(request) -> str:
    """Lấy JWT token từ session."""
    return request.session.get('jwt_token', '')


def _internal_headers(request) -> dict:
    """Headers cho request nội bộ đến microservices."""
    return {
        'X-Internal-Token': _get_jwt(request),
        'Content-Type': 'application/json',
    }


def _service_get(url: str, request=None, params=None, timeout=8):
    """Helper GET đến internal service với error handling."""
    try:
        headers = _internal_headers(request) if request else {}
        r = requests.get(url, headers=headers, params=params, timeout=timeout)
        return r.json() if r.ok else []
    except Exception as e:
        logger.warning(f"[GW] GET {url} thất bại: {e}")
        return []


def _service_post(url: str, request=None, data=None, timeout=8):
    """Helper POST đến internal service."""
    try:
        headers = _internal_headers(request) if request else {}
        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'
        r = requests.post(url, headers=headers, json=data or {}, timeout=timeout)
        return r.json(), r.status_code
    except Exception as e:
        logger.warning(f"[GW] POST {url} thất bại: {e}")
        return {}, 503


def _service_post_ai(url: str, request=None, data=None):
    """Helper POST chuyên dụng cho AI services (timeout 60s vì Gemini API cần 10-20s)."""
    return _service_post(url, request=request, data=data, timeout=60)


def login_required(view_func):
    """Decorator: yêu cầu đăng nhập, redirect về /login/ nếu chưa."""
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not request.session.get('account_id'):
            return redirect('/login/?next=' + request.path)
        return view_func(self, request, *args, **kwargs)
    return wrapper


# ══════════════════════════════════════════════════════════════════════════════
# INDEX – Trang chủ (danh sách sản phẩm)
# ══════════════════════════════════════════════════════════════════════════════

class IndexView(View):
    def get(self, request):
        account_id = request.session.get('account_id')

        # Lấy danh sách sản phẩm từ product-service
        q        = request.GET.get('q', '')
        category = request.GET.get('category', '')
        symptom  = request.GET.get('symptom', '')

        params = {}
        if q:        params['q']        = q
        if category: params['category'] = category
        if symptom:  params['symptom']  = symptom

        products = _service_get(f"{PHARMACY_URL}/products/", request, params=params)

        # Lấy điểm đánh giá trung bình cho từng sản phẩm
        if products:
            ids_str    = ','.join(str(p['id']) for p in products)
            review_summary = _service_get(
                f"{MED_REVIEW_URL}/reviews/summary/",
                request,
                params={'product_ids': ids_str},
            )
            # Fallback nếu service lỗi trả về []
            if not isinstance(review_summary, dict):
                review_summary = {}

            for p in products:
                pid = str(p['id'])
                p['avg_rating'] = review_summary.get(pid, {}).get('avg')
                p['review_count']= review_summary.get(pid, {}).get('count', 0)

        # Lấy danh mục từ medical-catalog-service
        categories = _service_get(f"{MED_CATALOG_URL}/categories/", request)

        # Lấy số lượng đơn thuốc tạm thời (prescription/cart)
        cart_count = 0
        if account_id:
            cart_items = _service_get(f"{PRESCRIPTION_URL}/carts/{account_id}/", request)
            cart_count = sum(item.get('quantity', 0) for item in cart_items)

        # AI Treatment Recommendations
        recommendations = []
        if account_id:
            recs = _service_get(
                f"{TREATMENT_REC_URL}/api/recommend/",
                request,
                params={'user_id': f"U{account_id}", 'top_k': 4},
            )
            rec_ids = [r['product_id'] for r in recs.get('recommendations', [])]
            recommendations = [p for p in products if p['id'] in rec_ids][:4]

        # Categories list for pill filters
        filter_categories = [
            ('antacid',      'Kháng acid'),
            ('ppi',          'PPI'),
            ('h2_blocker',   'H2 Blocker'),
            ('antibiotic',   'Kháng sinh'),
            ('probiotic',    'Probiotic'),
            ('antiemetic',   'Chống nôn'),
            ('mucosal',      'Bảo vệ niêm mạc'),
            ('antispasmodic','Chống co thắt'),
        ]

        return render(request, 'index.html', {
            'products':          products,
            'categories':        categories,
            'filter_categories': filter_categories,
            'search_q':          q,
            'search_category':   category,
            'cart_count':        cart_count,
            'account_id':        account_id,
            'username':          request.session.get('username', ''),
            'role':              request.session.get('role', ''),
            'recommendations':   recommendations,
        })


# ══════════════════════════════════════════════════════════════════════════════
# AUTH: Login / Register / Logout
# ══════════════════════════════════════════════════════════════════════════════

class LoginView(View):
    def get(self, request):
        if request.session.get('account_id'):
            return redirect('/')
        return render(request, 'login.html')

    def post(self, request):
        username    = request.POST.get('username', '').strip()
        raw_password = request.POST.get('password', '')

        if not username or not raw_password:
            return render(request, 'login.html', {'error': 'Vui lòng điền đầy đủ thông tin'})

        try:
            account = Account.objects.get(username=username, is_active=True)
        except Account.DoesNotExist:
            return render(request, 'login.html', {'error': 'Tên đăng nhập không tồn tại'})

        if account.password != hash_password(raw_password):
            return render(request, 'login.html', {'error': 'Mật khẩu không đúng'})

        # Lấy JWT từ auth-service
        jwt_data, status = _service_post(
            f"{AUTH_URL}/auth/login/",
            data={'user_id': account.id, 'username': account.username, 'role': account.role},
        )
        token = jwt_data.get('token', '')

        # Lưu vào session
        request.session['account_id'] = account.id
        request.session['username']   = account.username
        request.session['fullname']   = account.fullname
        request.session['role']       = account.role
        request.session['jwt_token']  = token

        logger.info(f"[GW] Đăng nhập thành công: {username} (role={account.role})")
        if account.role == 'admin':
            return redirect('/admin/dashboard/')
        next_url = request.GET.get('next', '/')
        return redirect(next_url)


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username    = request.POST.get('username', '').strip()
        raw_password = request.POST.get('password', '')
        fullname    = request.POST.get('fullname', '').strip()
        phone       = request.POST.get('phone', '').strip()
        email       = request.POST.get('email', '').strip()

        # Validation
        if not username or not raw_password or not fullname:
            return render(request, 'register.html', {'error': 'Cần điền đầy đủ tên đăng nhập, mật khẩu và họ tên'})

        if len(raw_password) < 6:
            return render(request, 'register.html', {'error': 'Mật khẩu phải có ít nhất 6 ký tự'})

        if Account.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': f'Tên đăng nhập "{username}" đã tồn tại'})

        # Tạo tài khoản
        account = Account.objects.create(
            username = username,
            password = hash_password(raw_password),
            fullname = fullname,
            phone    = phone,
            email    = email,
            role     = 'customer',
        )

        # Tạo hồ sơ bệnh nhân trong patient-service
        _service_post(f"{PATIENT_URL}/customers/", data={
            'account_id': account.id,
            'name':  fullname,
            'phone': phone,
            'email': email,
        })

        logger.info(f"[GW] Tài khoản mới: {username} (id={account.id} - Customer profile created)")

        # Auto-login sau đăng ký
        jwt_data, _ = _service_post(
            f"{AUTH_URL}/auth/login/",
            data={'user_id': account.id, 'username': account.username, 'role': account.role},
        )
        request.session['account_id'] = account.id
        request.session['username']   = account.username
        request.session['fullname']   = account.fullname
        request.session['role']       = account.role
        request.session['jwt_token']  = jwt_data.get('token', '')

        return redirect('/')


class LogoutView(View):
    def get(self, request):
        request.session.flush()
        return redirect('/login/')


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT DETAIL
# ══════════════════════════════════════════════════════════════════════════════

class ProductDetailView(View):
    def get(self, request, product_id):
        product = _service_get(f"{PHARMACY_URL}/products/{product_id}/", request)
        if not product:
            return render(request, '404.html', status=404)

        reviews = _service_get(
            f"{MED_REVIEW_URL}/reviews/",
            request,
            params={'product_id': product_id},
        )
        # Review summary
        reviews_summary = _service_get(
            f"{MED_REVIEW_URL}/reviews/summary/",
            request,
            params={'product_ids': str(product_id)},
        )
        if isinstance(reviews_summary, dict):
            reviews_summary = reviews_summary.get(str(product_id), {})

        cart_count = 0
        account_id = request.session.get('account_id')
        if account_id:
            cart_items = _service_get(f"{PRESCRIPTION_URL}/carts/{account_id}/", request)
            cart_count = sum(item.get('quantity', 0) for item in cart_items)

        return render(request, 'product_detail.html', {
            'product':         product,
            'reviews':         reviews,
            'reviews_summary': reviews_summary,
            'cart_count':      cart_count,
            'account_id':      account_id,
            'username':        request.session.get('username', ''),
        })


# ══════════════════════════════════════════════════════════════════════════════
# REVIEW SUBMIT (Viết đánh giá sản phẩm)
# ══════════════════════════════════════════════════════════════════════════════

class ReviewSubmitView(View):
    @login_required
    def post(self, request, product_id):
        account_id = request.session.get('account_id')
        rating     = int(request.POST.get('rating', 5))
        comment    = request.POST.get('comment', '').strip()
        treatment_effect = request.POST.get('treatment_effect', '')

        if not comment:
            messages.error(request, 'Vui lòng nhập nội dung đánh giá')
            return redirect(f'/products/{product_id}/')

        data = {
            'product_id':       product_id,
            'customer_id':      account_id,
            'rating':           rating,
            'comment':          comment,
        }
        if treatment_effect:
            try:
                data['treatment_effect'] = int(treatment_effect)
            except ValueError:
                pass

        result, status_code = _service_post(f"{MED_REVIEW_URL}/reviews/", request, data=data)

        if status_code in (200, 201):
            messages.success(request, 'Đã gửi đánh giá thành công!')
        else:
            err = result.get('error', 'Không thể gửi đánh giá')
            messages.error(request, err)

        return redirect(f'/products/{product_id}/')


# ══════════════════════════════════════════════════════════════════════════════
# CART
# ══════════════════════════════════════════════════════════════════════════════

class CartView(View):
    @login_required
    def get(self, request):
        account_id = request.session.get('account_id')
        cart_items = _service_get(f"{PRESCRIPTION_URL}/carts/{account_id}/", request)

        # Gắn thông tin thuốc vào từng dòng đơn thuốc tạm thời
        product_ids = list(set(item.get('product_id') for item in cart_items))
        products_map = {}
        for pid in product_ids:
            p = _service_get(f"{PHARMACY_URL}/products/{pid}/", request)
            if p:
                products_map[pid] = p

        enriched_items = []
        total = 0
        for item in cart_items:
            pid  = item.get('product_id')
            prod = products_map.get(pid, {})
            item['product'] = prod
            price = float(prod.get('price', 0)) if prod.get('price') else 0
            item['subtotal'] = price * item.get('quantity', 1)
            total += item['subtotal']
            enriched_items.append(item)

        return render(request, 'cart.html', {
            'cart_items': enriched_items,
            'total':      total,
            'cart_count': sum(item.get('quantity', 0) for item in cart_items),
            'username':   request.session.get('username', ''),
            'account_id': account_id,
        })


class CartAddView(View):
    @login_required
    def post(self, request):
        account_id = request.session.get('account_id')
        product_id = int(request.POST.get('product_id', 0))
        quantity   = int(request.POST.get('quantity', 1))

        if not product_id:
            messages.error(request, 'Sản phẩm không hợp lệ')
            return redirect('/')

        _service_post(f"{PRESCRIPTION_URL}/cart-items/", request, data={
            'customer_id': account_id,
            'product_id':  product_id,
            'quantity':    quantity,
        })

        messages.success(request, 'Đã thêm vào giỏ hàng!')
        next_url = request.POST.get('next', '/cart/')
        return redirect(next_url)


class CartRemoveView(View):
    @login_required
    def post(self, request, item_id):
        try:
            requests.delete(
                f"{PRESCRIPTION_URL}/cart-items/{item_id}/",
                headers=_internal_headers(request),
                timeout=5,
            )
        except Exception:
            pass
        return redirect('/cart/')


class CartPatchView(View):
    """AJAX PATCH: cập nhật số lượng 1 item trong giỏ hàng không reload trang."""
    @login_required
    def post(self, request, item_id):
        from django.http import JsonResponse
        quantity = request.POST.get('quantity')
        try:
            r = requests.patch(
                f"{PRESCRIPTION_URL}/cart-items/{item_id}/",
                json={'quantity': int(quantity)},
                headers=_internal_headers(request),
                timeout=5,
            )
            return JsonResponse({'ok': True, 'quantity': int(quantity)})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# ══════════════════════════════════════════════════════════════════════════════
# CHECKOUT / ORDERS
# ══════════════════════════════════════════════════════════════════════════════

class CheckoutView(View):
    @login_required
    def get(self, request):
        account_id = request.session.get('account_id')
        cart_items = _service_get(f"{PRESCRIPTION_URL}/carts/{account_id}/", request)

        enriched_items = []
        total = 0
        for item in cart_items:
            pid  = item.get('product_id')
            prod = _service_get(f"{PHARMACY_URL}/products/{pid}/", request) or {}
            item['product'] = prod
            price = float(prod.get('price', 0)) if prod.get('price') else 0
            item['subtotal'] = price * item.get('quantity', 1)
            total += item['subtotal']
            enriched_items.append(item)

        # Lấy địa chỉ đã lưu từ patient-service để pre-fill
        saved_address = ''
        try:
            profile_r = _service_get(f"{PATIENT_URL}/customers/by-account/{account_id}/", request)
            if isinstance(profile_r, dict):
                saved_address = profile_r.get('address', '')
        except Exception:
            pass

        return render(request, 'checkout.html', {
            'cart_items':       enriched_items,
            'total':            total,
            'username':         request.session.get('username', ''),
            'account_id':       account_id,
            'shipping_address': saved_address,
        })

    @login_required
    def post(self, request):
        account_id       = request.session.get('account_id')
        payment_method   = request.POST.get('payment_method', 'Cash')
        shipping_method  = request.POST.get('shipping_method', 'Standard')
        shipping_address = request.POST.get('shipping_address', '')
        note             = request.POST.get('note', '')
        try:
            discount_rate = float(request.POST.get('discount_rate', '0'))
            discount_rate = max(0.0, min(1.0, discount_rate))
        except (ValueError, TypeError):
            discount_rate = 0.0

        result, status_code = _service_post(
            f"{DISPENSING_URL}/orders/create/",
            request,
            data={
                'customer_id':     account_id,
                'payment_method':  payment_method,
                'shipping_method': shipping_method,
                'shipping_address': shipping_address,
                'note':            note,
                'discount_rate':   discount_rate,
            },
        )

        if status_code in (200, 201):
            order_id = result.get('id')
            messages.success(request, f'Đặt hàng thành công! Mã đơn hàng: #{order_id}')
            return redirect(f'/orders/{order_id}/')
        else:
            error = result.get('error', 'Đặt hàng thất bại')
            messages.error(request, error)
            return redirect('/checkout/')


class OrderHistoryView(View):
    @login_required
    def get(self, request):
        account_id = request.session.get('account_id')
        orders     = _service_get(
            f"{DISPENSING_URL}/orders/",
            request,
            params={'customer_id': account_id},
        )
        return render(request, 'order_history.html', {
            'orders':     orders,
            'username':   request.session.get('username', ''),
            'account_id': account_id,
            'cart_count': 0,
        })


class OrderDetailView(View):
    @login_required
    def get(self, request, order_id):
        order = _service_get(f"{DISPENSING_URL}/orders/{order_id}/", request)
        return render(request, 'order_detail.html', {
            'order':      order,
            'username':   request.session.get('username', ''),
            'account_id': request.session.get('account_id'),
        })


# ══════════════════════════════════════════════════════════════════════════════
# AI FEATURES
# ══════════════════════════════════════════════════════════════════════════════

class AIChatView(View):
    def get(self, request):
        return render(request, 'ai_chat.html', {
            'username':   request.session.get('username', ''),
            'account_id': request.session.get('account_id'),
            'cart_count': 0,
        })

    def post(self, request):
        """AJAX endpoint: nhận tin nhắn, gọi ai-consulting-service, trả về JSON."""
        import json
        from django.http import JsonResponse

        message     = request.POST.get('message', '').strip()
        account_id  = request.session.get('account_id')

        if not message:
            return JsonResponse({'error': 'Tin nhắn không được trống'}, status=400)

        result, status_code = _service_post_ai(
            f"{CLINICAL_ADV_URL}/api/chat",
            request,
            data={
                'message':     message,
                'customer_id': account_id,
            },
        )

        if status_code in (200, 201):
            return JsonResponse({
                'answer':       result.get('answer', ''),
                'intent':       result.get('intent', 'general'),
                'intent_label': result.get('intent_label', ''),
                'sources':      result.get('sources_count', 0),
                'mode':         result.get('mode', 'template'),
            })
        else:
            return JsonResponse({'error': 'AI service không phản hồi'}, status=503)


class AIRecommendView(View):
    @login_required
    def get(self, request):
        account_id = request.session.get('account_id')
        recs = _service_get(
            f"{TREATMENT_REC_URL}/api/recommend/",
            request,
            params={'user_id': f"U{account_id}", 'top_k': 8},
        )
        rec_list = recs.get('recommendations', []) if isinstance(recs, dict) else []
        # Lấy thông tin chi tiết từng sản phẩm thuốc
        products = []
        for rec in rec_list:
            pid = rec.get('product_id')
            p   = _service_get(f"{PHARMACY_URL}/products/{pid}/", request)
            if p:
                p['score']      = rec.get('score')
                p['gnn_score']  = rec.get('gnn_score')
                p['airm_score'] = rec.get('airm_score')
                products.append(p)

        return render(request, 'ai_recommend.html', {
            'products':   products,
            'username':   request.session.get('username', ''),
            'account_id': account_id,
            'cart_count': 0,
        })


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE
# ══════════════════════════════════════════════════════════════════════════════

class ProfileView(View):
    @login_required
    def get(self, request):
        account_id = request.session.get('account_id')
        profile_data = _service_get(f"{PATIENT_URL}/customers/by-account/{account_id}/", request)

        orders = _service_get(
            f"{DISPENSING_URL}/orders/",
            request,
            params={'customer_id': account_id},
        )
        return render(request, 'profile.html', {
            'profile':    profile_data,
            'orders':     orders,
            'username':   request.session.get('username', ''),
            'fullname':   request.session.get('fullname', ''),
            'account_id': account_id,
            'cart_count': 0,
        })


# ══════════════════════════════════════════════════════════════════════════════
# PROFILE – Settings
# ══════════════════════════════════════════════════════════════════════════════

class ProfileSettingsView(View):
    @login_required
    def post(self, request):
        account_id = request.session.get('account_id')

        fullname         = request.POST.get('fullname', '').strip()
        phone            = request.POST.get('phone', '').strip()
        email_val        = request.POST.get('email', '').strip()
        address          = request.POST.get('address', '').strip()
        blood_type       = request.POST.get('blood_type', '').strip()
        insurance_code   = request.POST.get('insurance_code', '').strip()

        if not fullname:
            # Re-render profile with error
            profile_data = _service_get(f"{PATIENT_URL}/patients/by-account/{account_id}/", request)
            orders = _service_get(f"{DISPENSING_URL}/orders/", request, params={'customer_id': account_id})
            return render(request, 'profile.html', {
                'profile': profile_data, 'orders': orders,
                'username':   request.session.get('username', ''),
                'fullname':   request.session.get('fullname', ''),
                'account_id': account_id, 'cart_count': 0,
                'settings_error': 'Họ tên không được để trống',
            })

        # Cập nhật Account local (fullname)
        Account.objects.filter(id=account_id).update(fullname=fullname)
        request.session['fullname'] = fullname

        # Cập nhật hồ sơ bệnh nhân qua patient-service
        profile_data = _service_get(f"{PATIENT_URL}/customers/by-account/{account_id}/", request)
        patient_id   = profile_data.get('id') if isinstance(profile_data, dict) else None
        
        if patient_id:
            update_data = {'name': fullname, 'phone': phone, 'email': email_val, 'address': address}
            if blood_type:     update_data['blood_type']     = blood_type
            if insurance_code: update_data['insurance_code'] = insurance_code

            try:
                requests.put(
                    f"{PATIENT_URL}/customers/by-account/{account_id}/",
                    headers=_internal_headers(request),
                    json=update_data,
                    timeout=8,
                )
            except Exception as e:
                logger.warning(f"[GW] Cập nhật patient {account_id} thất bại: {e}")
        else:
            # Nếu chưa có profile thì tự động tạo
            try:
                requests.post(
                    f"{PATIENT_URL}/customers/by-account/{account_id}/",
                    headers=_internal_headers(request),
                    json={'name': fullname, 'phone': phone, 'email': email_val, 'address': address},
                    timeout=8,
                )
            except Exception as e:
                logger.warning(f"[GW] Tạo mới patient {account_id} thất bại: {e}")

        # Re-fetch & render
        profile_data = _service_get(f"{PATIENT_URL}/customers/by-account/{account_id}/", request)
        orders = _service_get(f"{DISPENSING_URL}/orders/", request, params={'customer_id': account_id})
        return render(request, 'profile.html', {
            'profile': profile_data, 'orders': orders,
            'username':   request.session.get('username', ''),
            'fullname':   fullname,
            'account_id': account_id, 'cart_count': 0,
            'settings_success': 'Đã lưu thông tin thành công!',
        })


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

class HealthView(View):
    def get(self, request):
        from django.http import JsonResponse
        services_status = {}
        for name, url in [
            ('auth-service',                f"{AUTH_URL}/health/"),
            ('pharmacy-service',            f"{PHARMACY_URL}/health/"),
            ('patient-service',             f"{PATIENT_URL}/health/"),
            ('prescription-service',        f"{PRESCRIPTION_URL}/health/"),
            ('dispensing-service',          f"{DISPENSING_URL}/health/"),
            ('medical-review-service',      f"{MED_REVIEW_URL}/health/"),
            ('clinical-advisory-service',   f"{CLINICAL_ADV_URL}/health/"),
            ('treatment-recommender-service', f"{TREATMENT_REC_URL}/health/"),
        ]:
            try:
                r = requests.get(url, timeout=3)
                services_status[name] = 'UP' if r.ok else 'DOWN'
            except Exception:
                services_status[name] = 'DOWN'

        all_up = all(v == 'UP' for v in services_status.values())
        return JsonResponse({
            'status':   'UP' if all_up else 'DEGRADED',
            'gateway':  'UP',
            'services': services_status,
        })


# ------------------------------------------------------------------------------
# ADMIN PORTAL
# ------------------------------------------------------------------------------

def admin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped(self, request, *args, **kwargs):
        req = request if hasattr(request, 'session') else self
        if req.session.get('role') != 'admin':
            messages.error(req, 'Bạn không có quyền truy cập trang quản trị.')
            return redirect('/')
        return view_func(self, request, *args, **kwargs)
    return _wrapped


class AdminDashboardView(View):
    @admin_required
    def get(self, request):
        users_count   = Account.objects.exclude(role='admin').count()
        products_data = _service_get(f'{PHARMACY_URL}/products/', request) or []
        orders_data   = _service_get(f'{DISPENSING_URL}/orders/', request) or []
        pending_orders = [o for o in orders_data if o.get('status') == 'Pending'] if isinstance(orders_data, list) else []
        return render(request, 'admin/dashboard.html', {
            'users_count':    users_count,
            'products_count': len(products_data) if isinstance(products_data, list) else 0,
            'orders_count':   len(orders_data) if isinstance(orders_data, list) else 0,
            'pending_count':  len(pending_orders),
            'recent_orders':  orders_data[:10] if isinstance(orders_data, list) else [],
            'username': 'Admin',
        })


class AdminProductListView(View):
    @admin_required
    def get(self, request):
        products = _service_get(f'{PHARMACY_URL}/products/', request) or []
        return render(request, 'admin/products.html', {
            'products': products if isinstance(products, list) else [],
            'username': 'Admin',
        })


class AdminProductCreateView(View):
    @admin_required
    def get(self, request):
        return render(request, 'admin/product_form.html', {'product': None, 'username': 'Admin'})

    @admin_required
    def post(self, request):
        data = {
            'name': request.POST.get('name', ''),
            'generic_name': request.POST.get('generic_name', ''),
            'category': request.POST.get('category', 'other'),
            'price': request.POST.get('price', 0),
            'stock_quantity': request.POST.get('stock_quantity', 0),
            'unit': request.POST.get('unit', 'vien'),
            'dosage_strength': request.POST.get('dosage_strength', ''),
            'description': request.POST.get('description', ''),
            'requires_prescription': request.POST.get('requires_prescription') == 'on',
            'manufacturer': request.POST.get('manufacturer', ''),
        }
        result, status_code = _service_post(f'{PHARMACY_URL}/products/', request, data=data)
        if status_code in (200, 201):
            messages.success(request, f"Da them san pham.")
            return redirect('/admin/products/')
        messages.error(request, f"Loi them san pham.")
        return redirect('/admin/products/create/')


class AdminProductEditView(View):
    @admin_required
    def get(self, request, product_id):
        product = _service_get(f'{PHARMACY_URL}/products/{product_id}/', request) or {}
        return render(request, 'admin/product_form.html', {'product': product, 'username': 'Admin'})

    @admin_required
    def post(self, request, product_id):
        data = {
            'name': request.POST.get('name', ''),
            'generic_name': request.POST.get('generic_name', ''),
            'category': request.POST.get('category', 'other'),
            'price': request.POST.get('price', 0),
            'stock_quantity': request.POST.get('stock_quantity', 0),
            'unit': request.POST.get('unit', 'vien'),
            'dosage_strength': request.POST.get('dosage_strength', ''),
            'description': request.POST.get('description', ''),
            'requires_prescription': request.POST.get('requires_prescription') == 'on',
            'manufacturer': request.POST.get('manufacturer', ''),
        }
        try:
            r = requests.put(f'{PHARMACY_URL}/products/{product_id}/', json=data, headers=_internal_headers(request), timeout=8)
            if r.ok:
                messages.success(request, 'Da cap nhat san pham.')
                return redirect('/admin/products/')
            messages.error(request, f'Loi cap nhat.')
        except Exception as e:
            messages.error(request, f'Loi ket noi: {e}')
        return redirect(f'/admin/products/{product_id}/edit/')


class AdminProductDeleteView(View):
    @admin_required
    def post(self, request, product_id):
        try:
            requests.delete(f'{PHARMACY_URL}/products/{product_id}/', headers=_internal_headers(request), timeout=5)
            messages.success(request, 'Da xoa san pham.')
        except Exception as e:
            messages.error(request, f'Loi xoa: {e}')
        return redirect('/admin/products/')


class AdminOrderListView(View):
    @admin_required
    def get(self, request):
        orders = _service_get(f'{DISPENSING_URL}/orders/', request) or []
        accounts = {a.id: a.username for a in Account.objects.all()}
        for o in (orders if isinstance(orders, list) else []):
            o['customer_name'] = accounts.get(o.get('customer_id'), f"ID {o.get('customer_id')}")
        return render(request, 'admin/orders.html', {
            'orders': orders if isinstance(orders, list) else [],
            'username': 'Admin',
        })


class AdminOrderUpdateView(View):
    @admin_required
    def post(self, request, order_id):
        new_status = request.POST.get('status')
        try:
            requests.patch(f'{DISPENSING_URL}/orders/{order_id}/', json={'status': new_status}, headers=_internal_headers(request), timeout=5)
            messages.success(request, f'Cap nhat don #{order_id} thanh {new_status}')
        except Exception as e:
            messages.error(request, f'Loi: {e}')
        return redirect('/admin/orders/')


class AdminUserListView(View):
    @admin_required
    def get(self, request):
        users = list(Account.objects.exclude(role='admin').values('id', 'username', 'role'))
        return render(request, 'admin/users.html', {'users': users, 'username': 'Admin'})
