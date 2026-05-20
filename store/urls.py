from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),  # root of app
    path('logout/', views.admin_logout, name='logout'),
    
    # Products URLs
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('products/low-stock/', views.low_stock_products, name='low_stock_products'),
    
    path('categories/', views.category_list, name='category_list'),
    path('categories/add_category/', views.add_category, name='add_category'),
    path('category/edit_category/<int:id>/', views.edit_category, name='edit_category'),
    path('category/delete_category/<int:id>/', views.delete_category, name='delete_category'),
    
    # SubCategory URLs
    path('subcategories/', views.subcategory_list, name='subcategory_list'),
    path('subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('subcategories/edit/<int:pk>/', views.edit_subcategory, name='edit_subcategory'),
    path('subcategories/delete/<int:pk>/', views.delete_subcategory, name='delete_subcategory'),
    
    # Offer URLs
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/add/', views.add_offer, name='add_offer'),
    path('offers/edit/<int:pk>/', views.edit_offer, name='edit_offer'),
    path('offers/delete/<int:pk>/', views.delete_offer, name='delete_offer'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/view/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/edit/<int:pk>/', views.edit_order, name='edit_order'),
    path('orders/delete/<int:pk>/', views.delete_order, name='delete_order'),
    path('orders/invoice/<int:pk>/', views.invoice, name='invoice'),
    path('delivery/', views.delivery_list, name='delivery_list'),
    path('delivery/track/<int:pk>/', views.track_order, name='track_order'),
    path('delivery/update-status/<int:pk>/', views.update_delivery_status, name='update_delivery_status'),
    
    # Reports URLs
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/sales/download/', views.download_sales_report, name='download_sales_report'),
    path('reports/customers/', views.customer_report, name='customer_report'),
    path('reports/customers/download/', views.download_customer_report, name='download_customer_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/inventory/download/', views.download_inventory_report, name='download_inventory_report'),

    # Advanced Admin Reports (date range + PDF)
    path('reports/daily-sales/', views.daily_sales_report, name='daily_sales_report'),
    path('reports/daily-sales/download/', views.download_daily_sales_report, name='download_daily_sales_report'),
    path('reports/monthly-sales/', views.monthly_sales_report, name='monthly_sales_report'),
    path('reports/monthly-sales/download/', views.download_monthly_sales_report, name='download_monthly_sales_report'),
    path('reports/product-sales/', views.product_wise_sales_report, name='product_wise_sales_report'),
    path('reports/product-sales/download/', views.download_product_wise_sales_report, name='download_product_wise_sales_report'),
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/low-stock/download/', views.download_low_stock_report, name='download_low_stock_report'),
    path('reports/customer-purchase/', views.customer_purchase_report, name='customer_purchase_report'),
    path('reports/customer-purchase/download/', views.download_customer_purchase_report, name='download_customer_purchase_report'),
    path('reports/profit-loss/', views.profit_loss_report, name='profit_loss_report'),
    path('reports/profit-loss/download/', views.download_profit_loss_report, name='download_profit_loss_report'),
    
    # Payment Management URLs
    path('payments/', views.payment_dashboard, name='payment_dashboard'),
    path('payments/detail/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/update-status/<int:pk>/', views.update_payment_status, name='update_payment_status'),
    path('payments/export/', views.export_payments, name='export_payments'),

    # Invoice & Tax Management
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/generate/<int:order_pk>/', views.generate_invoice, name='generate_invoice'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/download/', views.download_invoice_pdf, name='download_invoice_pdf'),

    path('taxes/', views.tax_list, name='tax_list'),
    path('taxes/add/', views.add_tax, name='add_tax'),
    path('taxes/<int:pk>/edit/', views.edit_tax, name='edit_tax'),
    path('taxes/<int:pk>/delete/', views.delete_tax, name='delete_tax'),

    # Settings
    path('admin-settings/', views.settings_page, name='admin_settings'),
    path('change-password/', views.change_password, name='change_password'),

    
]


