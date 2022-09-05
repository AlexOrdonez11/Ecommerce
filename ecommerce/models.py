from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Cliente(models.Model):
	usuario = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
	nombre = models.CharField(max_length=200, null=True)
	correo = models.CharField(max_length=200, unique=True)

	def __str__(self):
		return self.nombre

class Categoria(models.Model):
	nombre = models.CharField(max_length=200)

	def __str__(self):
		return self.nombre

class Producto(models.Model):
	categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null = True)
	nombre = models.CharField(max_length=200)
	precio = models.FloatField()
	digital = models.BooleanField(default=False,null=True, blank=True)
	imagen = models.ImageField(null=True, blank=True)

	def __str__(self):
		return self.nombre

	@property
	def URLimagen(self):
		try:
			url = self.imagen.url
		except:
			url = ''
		return url

class Orden(models.Model):
	cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
	fecha = models.DateTimeField(auto_now_add=True)
	completada = models.BooleanField(default=False)
	trans_id = models.CharField(max_length=100, null=True)

	def __str__(self):
		return str(self.trans_id)

	@property
	def get_cart_total(self):
		orderitems = self.itemorden_set.all()
		total = sum([item.get_total for item in orderitems])
		return total 

	@property
	def get_cart_items(self):
		orderitems = self.itemorden_set.all()
		total = sum([item.cantidad for item in orderitems])
		return total

	@property
	def shipping(self):
		shipping = False
		items = self.itemorden_set.all()
		for i in items:
			if i.producto.digital == False:
				shipping = True
		return shipping

class ItemOrden(models.Model):
	producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
	orden = models.ForeignKey(Orden, on_delete=models.SET_NULL, null=True)
	cantidad = models.IntegerField(default=0, null=True, blank=True)
	fecha = models.DateTimeField(auto_now_add=True)
	@property
	def get_total(self):
		total = self.producto.precio * self.cantidad
		return total

class Shipping(models.Model):
	cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)
	orden = models.ForeignKey(Orden, on_delete=models.SET_NULL, null=True)
	direccion = models.CharField(max_length=200, null=False)
	ciudad = models.CharField(max_length=200, null=False)
	dpto = models.CharField(max_length=200, null=False)
	cod_postal = models.CharField(max_length=200, null=False)
	fecha = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.direccion

