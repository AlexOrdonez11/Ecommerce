from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
import json
import datetime
from .utils import guestOrder, cartData, recomendar
from .models import *
from .forms import createUser

def register(request):
    data = cartData(request)
    items_carrito = data['items_carrito']
    orden = data['orden']
    items = data['items']
    form = createUser()
    if request.method == 'POST':
        form = createUser(request.POST)
        if form.is_valid():
            try:
                clientes = Cliente.objects.get(correo=form.cleaned_data.get('email'))
            except Cliente.DoesNotExist:
                clientes=None
            if clientes is None:
                form.save()
                nombre = form.cleaned_data.get('first_name')
                nombre += " " + form.cleaned_data.get('last_name')
                Cliente.objects.get_or_create(
                    usuario= User.objects.get(username=form.cleaned_data.get('username')),
                    nombre= nombre,
                    correo= form.cleaned_data.get('email')
                )
                return redirect('login')
            else:
                messages.info(request, "Correo ya esta en uso")
    context = {'items':items, 'orden':orden, 'items_carrito':items_carrito, 'form':form}
    return render(request, 'ecommerce/register.html', context)

def loginPage(request):
    data = cartData(request)
    items_carrito = data['items_carrito']
    orden = data['orden']
    items = data['items']
    if request.method == 'POST':
        username = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=username, password=pwd)
        if user is not None:
            login(request, user)
            return redirect('tienda')
        else:
            messages.info(request, "Usuario o contraseña incorrectos")
    context = {'items':items, 'orden':orden, 'items_carrito':items_carrito}
    return render(request, 'ecommerce/login.html', context)

def logoutUser(request):
    logout(request)
    print('entra')
    return redirect('login')

def tienda(request):
    data = cartData(request)
    items_carrito = data['items_carrito']
    orden = data['orden']
    items = data['items']
    productos = Producto.objects.all()
    recom=recomendar(request)
    recomendaciones=recom['recomendaciones']
    context={'productos':productos, 'items_carrito':items_carrito, 'recomendaciones' : recomendaciones}
    return render(request, 'ecommerce/tienda.html', context)

def carrito(request):
    data = cartData(request)
    items_carrito = data['items_carrito']
    orden = data['orden']
    items = data['items']
    context = {'items':items, 'orden':orden, 'items_carrito':items_carrito}
    return render(request, 'ecommerce/carrito.html', context)

def checkout(request):
    data = cartData(request)
    items_carrito = data['items_carrito']
    orden = data['orden']
    items = data['items']
    context = {'items':items, 'orden':orden, 'items_carrito':items_carrito}
    return render(request, 'ecommerce/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']

	cliente = request.user.cliente
	producto = Producto.objects.get(id=productId)
	orden, created = Orden.objects.get_or_create(cliente=cliente, completada=False)

	itemorden, created = ItemOrden.objects.get_or_create(orden=orden, producto=producto)

	if action == 'add':
		itemorden.cantidad = (itemorden.cantidad + 1)
	elif action == 'remove':
		itemorden.cantidad = (itemorden.cantidad - 1)

	itemorden.save()

	if itemorden.cantidad <= 0:
		itemorden.delete()

	return JsonResponse('Item was added', safe=False)

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def processOrder(request):
    trans_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)
    if request.user.is_authenticated:
        cliente = request.user.cliente
        orden, created = Orden.objects.get_or_create(cliente=cliente, completada=False)
    else:
        cliente, orden = guestOrder(request, data)
    total = float(data['form']['total'])
    orden.trans_id = trans_id
    if total == orden.get_cart_total:
        orden.completada = True
    orden.save()
    if orden.shipping == True:
        Shipping.objects.create(
        cliente=cliente,
        orden=orden,
        direccion=data['shipping']['direccion'],
        ciudad=data['shipping']['ciudad'],
        dpto=data['shipping']['dpto'],
        cod_postal=data['shipping']['cod_postal'],
        )
    return JsonResponse('Payment submitted..', safe=False)


