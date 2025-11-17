"""
Serializers 4;O customers app.
"""

from rest_framework import serializers
from decimal import Decimal
from customers.models import CustomerGroup, Customer, CustomerTransaction


class CustomerGroupSerializer(serializers.ModelSerializer):
    """!5@80;870B>@ 4;O 3@C?? ?>:C?0B5;59"""

    members_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = CustomerGroup
        fields = [
            'id', 'name', 'description', 'discount_percent',
            'min_purchase_amount', 'is_active',
            'members_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerTransactionSerializer(serializers.ModelSerializer):
    """!5@80;870B>@ 4;O B@0=70:F89 ?>:C?0B5;O"""

    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)

    class Meta:
        model = CustomerTransaction
        fields = [
            'id', 'customer', 'customer_name', 'transaction_type', 'transaction_type_display',
            'amount', 'balance_before', 'balance_after',
            'sale', 'description', 'performed_by', 'created_at'
        ]
        read_only_fields = ['id', 'balance_before', 'balance_after', 'created_at']


class CustomerSerializer(serializers.ModelSerializer):
    """!5@80;870B>@ 4;O ?>:C?0B5;59"""

    group_name = serializers.CharField(source='group.name', read_only=True, allow_null=True)
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)

    # KG8A;O5<K5 ?>;O
    full_name = serializers.CharField(read_only=True)
    available_credit = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    default_discount = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    is_vip = serializers.BooleanField(read_only=True)

    class Meta:
        model = Customer
        fields = [
            'id', 'first_name', 'last_name', 'middle_name', 'full_name',
            'customer_type', 'customer_type_display',
            'company_name', 'tax_id',
            'phone', 'phone_2', 'email',
            'address', 'city', 'region', 'postal_code',
            'group', 'group_name',
            'balance', 'credit_limit', 'available_credit',
            'loyalty_points', 'total_purchases', 'total_purchases_count',
            'default_discount', 'is_vip',
            'birthday', 'notes',
            'is_active', 'is_blocked',
            'created_at', 'updated_at', 'last_purchase_at'
        ]
        read_only_fields = [
            'id', 'balance', 'loyalty_points', 'total_purchases',
            'total_purchases_count', 'last_purchase_at',
            'created_at', 'updated_at'
        ]

    def validate_phone(self, value):
        """0;840F8O C=8:0;L=>AB8 B5;5D>=0"""
        # @>25@O5< B>;L:> ?@8 A>740=88 8;8 87<5=5=88 B5;5D>=0
        instance = self.instance
        if instance and instance.phone == value:
            return value

        if Customer.objects.filter(phone=value).exists():
            raise serializers.ValidationError('>:C?0B5;L A B0:8< =><5@>< B5;5D>=0 C65 ACI5AB2C5B')

        return value

    def validate(self, data):
        """0;840F8O ?>:C?0B5;O"""
        customer_type = data.get('customer_type', self.instance.customer_type if self.instance else 'individual')

        # ;O :><?0=89 >1O70B5;L=> =0720=85 :><?0=88
        if customer_type == 'company':
            company_name = data.get('company_name')
            if not company_name:
                raise serializers.ValidationError({
                    'company_name': ';O N@848G5A:>3> ;8F0 >1O70B5;L=> C:068B5 =0720=85 :><?0=88'
                })

        return data


class CustomerDetailSerializer(CustomerSerializer):
    """5B0;L=K9 A5@80;870B>@ 4;O ?>:C?0B5;O A B@0=70:F8O<8"""

    transactions = CustomerTransactionSerializer(many=True, read_only=True)
    recent_transactions = serializers.SerializerMethodField()

    class Meta(CustomerSerializer.Meta):
        fields = CustomerSerializer.Meta.fields + ['transactions', 'recent_transactions']

    def get_recent_transactions(self, obj):
        """>A;54=85 10 B@0=70:F89"""
        transactions = obj.transactions.all()[:10]
        return CustomerTransactionSerializer(transactions, many=True).data


class CustomerCreateUpdateSerializer(serializers.ModelSerializer):
    """!5@80;870B>@ 4;O A>740=8O/>1=>2;5=8O ?>:C?0B5;O"""

    class Meta:
        model = Customer
        fields = [
            'first_name', 'last_name', 'middle_name',
            'customer_type', 'company_name', 'tax_id',
            'phone', 'phone_2', 'email',
            'address', 'city', 'region', 'postal_code',
            'group', 'credit_limit', 'birthday', 'notes',
            'is_active', 'is_blocked'
        ]

    def validate_phone(self, value):
        """0;840F8O C=8:0;L=>AB8 B5;5D>=0"""
        instance = self.instance
        if instance and instance.phone == value:
            return value

        if Customer.objects.filter(phone=value).exists():
            raise serializers.ValidationError('>:C?0B5;L A B0:8< =><5@>< B5;5D>=0 C65 ACI5AB2C5B')

        return value

    def validate(self, data):
        """0;840F8O ?>:C?0B5;O"""
        customer_type = data.get('customer_type', self.instance.customer_type if self.instance else 'individual')

        # ;O :><?0=89 >1O70B5;L=> =0720=85 :><?0=88
        if customer_type == 'company':
            company_name = data.get('company_name')
            if not company_name:
                raise serializers.ValidationError({
                    'company_name': ';O N@848G5A:>3> ;8F0 >1O70B5;L=> C:068B5 =0720=85 :><?0=88'
                })

        return data


class CustomerBalanceSerializer(serializers.Serializer):
    """!5@80;870B>@ 4;O >?5@0F89 A 10;0=A><"""

    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)

    def validate_amount(self, value):
        """0;840F8O AC<<K"""
        if value <= 0:
            raise serializers.ValidationError('!C<<0 4>;6=0 1KBL 1>;LH5 =C;O')
        return value
