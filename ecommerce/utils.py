import json
from .models import *
import random as rd 
import pandas as pd 
import numpy as np
import sqlite3 as sql

def cookieCart(request):
	#Create empty cart for now for non-logged in user
    try:
        cart = json.loads(request.COOKIES['cart'])
    except:
        cart = {}
    print('CART:', cart)
    items = []
    orden = {'get_cart_total':0, 'get_cart_items':0, 'shipping':False}
    items_carrito = orden['get_cart_items']
    for i in cart:
        try:
            items_carrito += cart[i]['cantidad']
            producto = Producto.objects.get(id=i)
            total = (producto.precio * cart[i]['cantidad'])
            orden['get_cart_total'] += total
            orden['get_cart_items'] += cart[i]['cantidad']
            item = {
                'producto':{
                    'categoria':producto.categoria,
                    'id':producto.id,
                    'nombre':producto.nombre, 
                    'precio':producto.precio, 
                    'URLimagen':producto.URLimagen
                }, 
                'cantidad':cart[i]['cantidad'],
                'get_total':total,
                }
            items.append(item)
            if producto.digital == False:
                shipping = True
        except:
            pass
        if shipping:
            orden['shipping'] = shipping 
    context = {'items':items, 'orden':orden, 'items_carrito':items_carrito}
    return context

def cartData(request):
    if request.user.is_authenticated:
        cliente = request.user.cliente
        orden, created = Orden.objects.get_or_create(cliente=cliente, completada=False)
        items = orden.itemorden_set.all()
        items_carrito = orden.get_cart_items
    else:
        #Create empty cart for now for non-logged in user
        cookieData = cookieCart(request)
        items_carrito = cookieData['items_carrito']
        orden = cookieData['orden']
        items = cookieData['items']
    context = {'items':items, 'orden':orden, 'items_carrito':items_carrito}
    return context

def guestOrder(request, data):
    print('User is not logged in')
    print('COOKIES: ', request.COOKIES)
    nombre = data['form']['nombre']
    correo = data['form']['correo']
    cookieData = cookieCart(request)
    items = cookieData['items']
    cliente, created = Cliente.objects.get_or_create(correo=correo,)
    cliente.nombre = nombre
    cliente.save()
    orden = Orden.objects.create(cliente=cliente, completada=False,)
    for item in items:
        producto = Producto.objects.get(id = item['producto']['id'])
        item_orden = ItemOrden.objects.create(producto=producto, 
        orden=orden, cantidad=item['cantidad'],)
    return cliente, orden

def recomendar(request):
    con=sql.connect('./db.sqlite3')
    cur=con.cursor()
    cur.execute("SELECT cliente_id,producto_id,categoria_id FROM ecommerce_orden,ecommerce_itemorden,ecommerce_producto WHERE ecommerce_orden.id=ecommerce_itemorden.orden_id and ecommerce_itemorden.producto_id=ecommerce_producto.id")
    rows=cur.fetchall()
    hol=pd.DataFrame(rows,columns=[x[0] for x in cur.description])
    if request.user.is_authenticated:
        cliente = request.user.cliente.id
        print("========================================")
        print(cliente)
        if hol[hol.cliente_id == cliente].empty: 
            recomen=rec_cold(hol)
        else:
            products=hol[['producto_id','categoria_id']]
            g=hol[hol.cliente_id==cliente].groupby(['categoria_id']).count().reset_index()['categoria_id']
            recomen=recom_election(cliente,hol)
            cats=[]
            for index,row in products.iterrows():
                for r in recomen:
                    if r==row['producto_id']:
                        cats.append(row['categoria_id'])
            corrects=0
            print(g)
            print(cats)
            for gs in g:
                for cat in cats:
                    if cat==gs:
                        corrects=corrects+1
            
            print(corrects/len(recomen))
    else:
        recomen=rec_cold(hol)
    recomendados=[]
    for i in recomen:
        recomendados.append(Producto.objects.get(id=i))
    context = {'recomendaciones': recomendados }
    return context

def recom_election(x,hol):
    res=evaluate(hol)
    rec=recomendations(hol,res,x)
    return rec

def knn(hol,cliente):
    tabla=pd.DataFrame()
    hola=hol[['cliente_id','categoria_id']]
    h=hola.groupby(['cliente_id']).count().reset_index()
    tabla['cliente']=h['cliente_id']
    hola1=hola[hola.categoria_id == 1].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola1.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c1']=temp

    hola2=hola[hola.categoria_id == 2].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola2.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c2']=temp

    hola3=hola[hola.categoria_id == 3].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola3.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c3']=temp
    hola4=hola[hola.categoria_id == 4].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola4.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c4']=temp
    unit=tabla[tabla.cliente==cliente]
    pesos=[]
    for index1,row1 in tabla.iterrows():
        d1=(row1["c1"]-unit["c1"])**2
        d2=(row1["c2"]-unit["c2"])**2
        d3=(row1["c3"]-unit["c3"])**2
        d4=(row1["c4"]-unit["c4"])**2
        d=np.sqrt(d1+d2+d3+d4)
        pesos.append(d)
    
    tabla[['distancia']]=pesos
    print (tabla)
    grupo=tabla.sort_values(by=['distancia'])['cliente'].head(int(len(tabla)/3+1))
    repetidos=hol[hol.cliente_id == cliente][['producto_id','categoria_id']].groupby(['producto_id']).count().reset_index()['producto_id']
    recom=pd.DataFrame()
    recomendaciones=[]
    for index,row in hol.iterrows():
        agr=True
        for row1 in grupo:
            if row['cliente_id']==row1:
                for row2 in repetidos:
                    if row2==row['producto_id']:
                        agr=False
                if agr:
                    repetidos=repetidos.append(pd.Series(row['producto_id']), ignore_index=True)
                    recomendaciones.append(row['producto_id'])

    return recomendaciones

def rec_cold(hol):
    p=hol.groupby(['producto_id']).count()['cliente_id'].reset_index().sort_values(by=['cliente_id'],ascending=False)
    recomendation=p.head(3)['producto_id']
    return recomendation

def recomendations(hol,res,cliente):
    for index,row in res.iterrows():
        if cliente == row['cliente']:
            cluster = row['Cluster']
    grupo=res[res.Cluster == cluster]['cliente'].reset_index(drop=True)
    print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
    print(hol)
    print("-------------------")
    #print (grupo)    
    repetidos=hol[hol.cliente_id == cliente][['producto_id','categoria_id']].groupby(['producto_id']).count().reset_index()['producto_id']
    recom=pd.DataFrame()
    recomendaciones=[]
    for index,row in hol.iterrows():
        agr=True
        for row1 in grupo:
            if row['cliente_id']==row1:
                for row2 in repetidos:
                    if row2==row['producto_id']:
                        agr=False
                if agr:
                    repetidos=repetidos.append(pd.Series(row['producto_id']), ignore_index=True)
                    recomendaciones.append(row['producto_id'])

    return recomendaciones

def evaluate(hol):
    tabla=pd.DataFrame()
    hola=hol[['cliente_id','categoria_id']]
    h=hola.groupby(['cliente_id']).count().reset_index()
    tabla['cliente']=h['cliente_id']
    hola1=hola[hola.categoria_id == 1].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola1.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c1']=temp

    hola2=hola[hola.categoria_id == 2].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola2.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c2']=temp

    hola3=hola[hola.categoria_id == 3].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola3.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c3']=temp
    hola4=hola[hola.categoria_id == 4].groupby(['cliente_id']).count().reset_index()
    temp=[]
    for index1,row1 in tabla.iterrows():
        boolean=True
        for index2,row2 in hola4.iterrows():
            if row1['cliente']==row2['cliente_id']:
                temp.append(row2["categoria_id"])
                boolean=False
        if boolean:
            temp.append(0)
    tabla['c4']=temp
    print(tabla)
    K=3
    X=tabla[["c1","c2","c3","c4"]]
    Centroids=(X.sample(n=1))
    max=0
    posi=pd.DataFrame()
    for index1,row1 in X.iterrows():
        d1=(row1["c1"]-Centroids["c1"])**2
        d2=(row1["c2"]-Centroids["c2"])**2
        d3=(row1["c3"]-Centroids["c3"])**2
        d4=(row1["c4"]-Centroids["c4"])**2
        d=np.sqrt(d1+d2+d3+d4)
        x=d.iloc[0]
        if x > max:
            max=x
            posi=row1
    Centroids=Centroids.append(posi)
    Result=kmeans(2,Centroids,X)
    if K>2:
        for j in range(K-2):
            CentMax=0
            NewCent=(X.sample(n=1))
            for i in range(1,len(Centroids)+1):
                C1=Result[Result.Cluster == i]
                MaxTemp=C1[i].max()
                if CentMax < MaxTemp:
                    CentMax=MaxTemp
                    NewCent=C1[C1[i] == CentMax]
            temp=NewCent[["c1","c2","c3","c4"]]
            Centroids=Centroids.append(temp)
            X=X[["c1","c2","c3","c4"]]
            Result=kmeans(j+3,Centroids,X)
           
    #print(Centroids)
    print("==========================================")
    Result['cliente']=tabla['cliente']
    print (Result)
    return Result
    

def kmeans(K,Centroids,X):
    diff=1
    j=0
    while(diff!=0):
        XD=X
        i=1
        for index1,row_c in Centroids.iterrows():
            ED=[]
            for index2,row_d in XD.iterrows():
                d1=(row_c["c1"]-row_d["c1"])**2
                d2=(row_c["c2"]-row_d["c2"])**2
                d3=(row_c["c3"]-row_d["c3"])**2
                d4=(row_c["c4"]-row_d["c4"])**2
                d=np.sqrt(d1+d2+d3+d4)
                ED.append(d)
            X[i]=ED
            print (X) 
            i=i+1

        C=[]
        for index,row in X.iterrows():
            min_dist=row[1]
            pos=1
            for i in range(K):
                if row[i+1] < min_dist:
                    min_dist=row[i+1]
                    pos=i+1
            C.append(pos)
        X["Cluster"]=C
        Centroids_new = X.groupby(["Cluster"]).mean()[["c1","c2","c3","c4"]]
        if j == 0:
            diff=1
            j=j+1
        else:
            diff = (Centroids_new['c1'] - Centroids['c1']).sum() + (Centroids_new['c2'] - Centroids['c2']).sum() + (Centroids_new['c3'] - Centroids['c3']).sum() + (Centroids_new['c4'] - Centroids['c4']).sum()
        Centroids = X.groupby(["Cluster"]).mean()[["c1","c2","c3","c4"]]
        return X

        





    