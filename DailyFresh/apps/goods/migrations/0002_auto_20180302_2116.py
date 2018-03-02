# Generated by Django 2.0.2 on 2018-03-02 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goodsimage',
            name='sku',
            field=models.ForeignKey(on_delete=False, to='goods.GoodsSKU', verbose_name='商品SKU'),
        ),
        migrations.AlterField(
            model_name='goodssku',
            name='category',
            field=models.ForeignKey(on_delete=False, to='goods.GoodsCategory', verbose_name='类别'),
        ),
        migrations.AlterField(
            model_name='goodssku',
            name='goods',
            field=models.ForeignKey(on_delete=False, to='goods.Goods', verbose_name='商品'),
        ),
        migrations.AlterField(
            model_name='indexcategorygoodsbanner',
            name='category',
            field=models.ForeignKey(on_delete=False, to='goods.GoodsCategory', verbose_name='商品类别'),
        ),
        migrations.AlterField(
            model_name='indexcategorygoodsbanner',
            name='sku',
            field=models.ForeignKey(on_delete=False, to='goods.GoodsSKU', verbose_name='商品SKU'),
        ),
        migrations.AlterField(
            model_name='indexgoodsbanner',
            name='sku',
            field=models.ForeignKey(on_delete=False, to='goods.GoodsSKU', verbose_name='商品SKU'),
        ),
    ]
