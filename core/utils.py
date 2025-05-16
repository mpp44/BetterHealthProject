from functools import wraps
from django.shortcuts import redirect

def staff_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'staff_user_id' not in request.session:
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.session.get('staff_user_role') != role:
                return redirect('admin_login')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator