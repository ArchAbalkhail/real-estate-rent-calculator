#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حاسبة الإيجار العقاري - Python Backend
تحليل التدفقات النقدية المتقدم لتحديد أعلى قيمة إيجار مع ضمان الربحية

المؤلف: نظام حاسبة الإيجار العقاري
التاريخ: 2025
"""

import json
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContractInputs:
    """بيانات العقد الأساسية"""
    contract_duration: int = 20  # مدة العقد بالسنوات
    grace_period: int = 2  # فترة السماح بالسنوات
    rent_increase_interval: int = 5  # فترة الزيادة الإيجارية
    rent_increase_rate: float = 10.0  # نسبة الزيادة الإيجارية %
    capitalization_rate: float = 7.0  # معدل الرسملة %


@dataclass
class PropertyInputs:
    """بيانات العقار والتطوير"""
    land_area: float = 10000.0  # مساحة الأرض م²
    building_factor: float = 2.5  # معامل البناء
    building_ratio: float = 60.0  # نسبة البناء %
    construction_cost_per_sqm: float = 2000.0  # تكلفة البناء ريال/م²
    landscaping_cost_per_sqm: float = 500.0  # تكلفة تنسيق الموقع ريال/م²
    infrastructure_cost_per_sqm: float = 3000.0  # تكلفة البنية التحتية ريال/م²
    development_years: int = 2  # سنوات التنفيذ


@dataclass
class CostRatios:
    """نسب التكاليف الإضافية"""
    design_cost_ratio: float = 7.0  # نسبة تكاليف التصميم %
    supervision_cost_ratio: float = 5.0  # نسبة تكاليف الإشراف %
    contingency_cost_ratio: float = 2.0  # نسبة تكاليف الطوارئ %


@dataclass
class CashFlowItem:
    """عنصر التدفق النقدي السنوي"""
    year: int
    annual_rent: float
    discounted_cash_flow: float
    cumulative_cash_flow: float
    rent_increase_rate: float = 0.0


class RealEstateCalculator:
    """حاسبة الإيجار العقاري المتقدمة"""
    
    def __init__(self, contract: ContractInputs, property_data: PropertyInputs, cost_ratios: CostRatios):
        self.contract = contract
        self.property = property_data
        self.costs = cost_ratios
        self._calculated_costs = None
    
    def calculate_development_costs(self) -> Dict[str, float]:
        """حساب تكاليف التطوير الإجمالية"""
        if self._calculated_costs is not None:
            return self._calculated_costs
        
        # حساب المساحات
        buildable_area = self.property.land_area * self.property.building_factor
        remaining_area = self.property.land_area * (1 - self.property.building_ratio / 100)
        
        # حساب التكاليف الأساسية
        construction_cost = buildable_area * self.property.construction_cost_per_sqm
        landscaping_cost = remaining_area * self.property.landscaping_cost_per_sqm
        infrastructure_cost = self.property.land_area * self.property.infrastructure_cost_per_sqm
        
        # إجمالي التكاليف الأساسية
        basic_costs = construction_cost + landscaping_cost + infrastructure_cost
        
        # التكاليف الإضافية
        design_cost = basic_costs * (self.costs.design_cost_ratio / 100)
        supervision_cost = basic_costs * (self.costs.supervision_cost_ratio / 100)
        contingency_cost = basic_costs * (self.costs.contingency_cost_ratio / 100)
        
        # إجمالي التكاليف
        total_additional_costs = design_cost + supervision_cost + contingency_cost
        total_development_cost = basic_costs + total_additional_costs
        
        self._calculated_costs = {
            'buildable_area': buildable_area,
            'remaining_area': remaining_area,
            'construction_cost': construction_cost,
            'landscaping_cost': landscaping_cost,
            'infrastructure_cost': infrastructure_cost,
            'basic_costs': basic_costs,
            'design_cost': design_cost,
            'supervision_cost': supervision_cost,
            'contingency_cost': contingency_cost,
            'total_additional_costs': total_additional_costs,
            'total_development_cost': total_development_cost
        }
        
        return self._calculated_costs
    
    def calculate_npv(self, annual_rent: float) -> Tuple[float, List[CashFlowItem]]:
        """
        حساب صافي القيمة الحالية والتدفقات النقدية
        
        Args:
            annual_rent: الإيجار السنوي الأساسي
            
        Returns:
            tuple: (صافي القيمة الحالية, قائمة التدفقات النقدية)
        """
        development_costs = self.calculate_development_costs()
        total_cost = development_costs['total_development_cost']
        
        # البدء بالتكلفة الأولية (قيمة سالبة)
        npv = -total_cost
        cumulative_cash_flow = -total_cost
        cash_flows = []
        
        current_rent = annual_rent
        
        for year in range(1, self.contract.contract_duration + 1):
            yearly_rent = 0.0
            increase_rate = 0.0
            
            # تطبيق منطق بدء الإيجار بعد فترة السماح
            if year > self.contract.grace_period:
                yearly_rent = current_rent
                
                # تطبيق الزيادات الدورية
                if (year > self.contract.grace_period and 
                    (year - self.contract.grace_period - 1) % self.contract.rent_increase_interval == 0 and 
                    year > self.contract.grace_period + 1):
                    
                    increase_rate = self.contract.rent_increase_rate
                    current_rent *= (1 + self.contract.rent_increase_rate / 100)
                    yearly_rent = current_rent
            
            # حساب التدفق المخصوم
            discount_factor = (1 + self.contract.capitalization_rate / 100) ** year
            discounted_cash_flow = yearly_rent / discount_factor
            
            # تحديث NPV والتدفق التراكمي
            npv += discounted_cash_flow
            cumulative_cash_flow += discounted_cash_flow
            
            # إضافة عنصر التدفق النقدي
            cash_flows.append(CashFlowItem(
                year=year,
                annual_rent=yearly_rent,
                discounted_cash_flow=discounted_cash_flow,
                cumulative_cash_flow=cumulative_cash_flow,
                rent_increase_rate=increase_rate
            ))
        
        return npv, cash_flows
    
    def find_optimal_rent(self, tolerance: float = 1000.0, max_iterations: int = 100) -> Dict[str, float]:
        """
        البحث عن أعلى إيجار مربح باستخدام البحث الثنائي المحسن
        
        Args:
            tolerance: دقة البحث (ريال)
            max_iterations: عدد التكرارات القصوى
            
        Returns:
            dict: النتائج المحسوبة
        """
        low = 0.0
        high = 100_000_000.0  # 100 مليون كحد أقصى
        optimal_rent = 0.0
        optimal_npv = float('-inf')
        iterations = 0
        
        while high - low > tolerance and iterations < max_iterations:
            mid = (low + high) / 2
            npv, _ = self.calculate_npv(mid)
            
            if npv >= 0:
                optimal_rent = mid
                optimal_npv = npv
                low = mid
            else:
                high = mid
            
            iterations += 1
        
        # حساب النتائج التفصيلية للإيجار الأمثل
        final_npv, cash_flows = self.calculate_npv(optimal_rent)
        
        # حساب فترة الاسترداد
        payback_period = self._calculate_payback_period(cash_flows)
        
        # حساب معدل العائد الداخلي
        irr = self._calculate_irr(cash_flows)
        
        # حساب إجمالي العوائد
        total_returns = sum(cf.annual_rent for cf in cash_flows)
        average_annual_return = total_returns / self.contract.contract_duration if self.contract.contract_duration > 0 else 0
        
        development_costs = self.calculate_development_costs()
        
        return {
            'optimal_annual_rent': optimal_rent,
            'npv': final_npv,
            'payback_period': payback_period,
            'irr': irr,
            'total_returns': total_returns,
            'average_annual_return': average_annual_return,
            'total_development_cost': development_costs['total_development_cost'],
            'iterations': iterations,
            'cash_flows': cash_flows
        }
    
    def _calculate_payback_period(self, cash_flows: List[CashFlowItem]) -> float:
        """حساب فترة الاسترداد"""
        for i, cf in enumerate(cash_flows):
            if cf.cumulative_cash_flow >= 0:
                if i == 0:
                    return 1.0
                
                # تقدير دقيق للفترة باستخدام الاستيفاء الخطي
                prev_cf = cash_flows[i-1]
                ratio = abs(prev_cf.cumulative_cash_flow) / (cf.cumulative_cash_flow - prev_cf.cumulative_cash_flow)
                return i + ratio
        
        return float(self.contract.contract_duration)
    
    def _calculate_irr(self, cash_flows: List[CashFlowItem], max_iterations: int = 1000) -> float:
        """حساب معدل العائد الداخلي باستخدام طريقة نيوتن-رافسون"""
        development_costs = self.calculate_development_costs()
        initial_investment = development_costs['total_development_cost']
        
        # تحضير التدفقات النقدية
        flows = [-initial_investment] + [cf.annual_rent for cf in cash_flows]
        
        # تقدير أولي لمعدل العائد
        irr_guess = 0.1  # 10%
        
        for _ in range(max_iterations):
            # حساب NPV ومشتقته
            npv = 0
            npv_derivative = 0
            
            for t, flow in enumerate(flows):
                factor = (1 + irr_guess) ** t
                npv += flow / factor
                if t > 0:
                    npv_derivative -= t * flow / ((1 + irr_guess) ** (t + 1))
            
            # تحديث التقدير
            if abs(npv_derivative) < 1e-10:
                break
            
            new_guess = irr_guess - npv / npv_derivative
            
            # التحقق من التقارب
            if abs(new_guess - irr_guess) < 1e-8:
                irr_guess = new_guess
                break
            
            irr_guess = new_guess
            
            # تجنب القيم السالبة المفرطة
            if irr_guess < -0.99:
                irr_guess = -0.99
        
        return irr_guess * 100  # تحويل إلى نسبة مئوية
    
    def sensitivity_analysis(self, parameter: str, variations: List[float]) -> List[Dict]:
        """
        تحليل الحساسية لمعرفة تأثير تغيير المعاملات
        
        Args:
            parameter: اسم المعامل المراد تحليله
            variations: قائمة القيم المختلفة للاختبار
            
        Returns:
            list: نتائج التحليل لكل قيمة
        """
        results = []
        original_value = getattr(self.contract, parameter, None) or getattr(self.property, parameter, None) or getattr(self.costs, parameter, None)
        
        for variation in variations:
            # تحديث القيمة مؤقتاً
            if hasattr(self.contract, parameter):
                setattr(self.contract, parameter, variation)
            elif hasattr(self.property, parameter):
                setattr(self.property, parameter, variation)
            elif hasattr(self.costs, parameter):
                setattr(self.costs, parameter, variation)
            
            # إعادة تعيين التكاليف المحسوبة
            self._calculated_costs = None
            
            # حساب النتائج
            result = self.find_optimal_rent()
            result[parameter] = variation
            results.append(result)
        
        # استعادة القيمة الأصلية
        if hasattr(self.contract, parameter):
            setattr(self.contract, parameter, original_value)
        elif hasattr(self.property, parameter):
            setattr(self.property, parameter, original_value)
        elif hasattr(self.costs, parameter):
            setattr(self.costs, parameter, original_value)
        
        self._calculated_costs = None
        
        return results
    
    def export_to_json(self, filename: str = None) -> str:
        """تصدير النتائج إلى ملف JSON"""
        results = self.find_optimal_rent()
        
        # تحويل CashFlowItem إلى dict
        cash_flows_dict = []
        for cf in results['cash_flows']:
            cash_flows_dict.append({
                'year': cf.year,
                'annual_rent': cf.annual_rent,
                'discounted_cash_flow': cf.discounted_cash_flow,
                'cumulative_cash_flow': cf.cumulative_cash_flow,
                'rent_increase_rate': cf.rent_increase_rate
            })
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'inputs': {
                'contract': {
                    'contract_duration': self.contract.contract_duration,
                    'grace_period': self.contract.grace_period,
                    'rent_increase_interval': self.contract.rent_increase_interval,
                    'rent_increase_rate': self.contract.rent_increase_rate,
                    'capitalization_rate': self.contract.capitalization_rate
                },
                'property': {
                    'land_area': self.property.land_area,
                    'building_factor': self.property.building_factor,
                    'building_ratio': self.property.building_ratio,
                    'construction_cost_per_sqm': self.property.construction_cost_per_sqm,
                    'landscaping_cost_per_sqm': self.property.landscaping_cost_per_sqm,
                    'infrastructure_cost_per_sqm': self.property.infrastructure_cost_per_sqm,
                    'development_years': self.property.development_years
                },
                'cost_ratios': {
                    'design_cost_ratio': self.costs.design_cost_ratio,
                    'supervision_cost_ratio': self.costs.supervision_cost_ratio,
                    'contingency_cost_ratio': self.costs.contingency_cost_ratio
                }
            },
            'calculated_costs': self.calculate_development_costs(),
            'results': {
                'optimal_annual_rent': results['optimal_annual_rent'],
                'npv': results['npv'],
                'payback_period': results['payback_period'],
                'irr': results['irr'],
                'total_returns': results['total_returns'],
                'average_annual_return': results['average_annual_return'],
                'total_development_cost': results['total_development_cost'],
                'iterations': results['iterations']
            },
            'cash_flows': cash_flows_dict
        }
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return filename
        else:
            return json.dumps(export_data, ensure_ascii=False, indent=2)


def main():
    """دالة رئيسية لاختبار الحاسبة"""
    # إعداد البيانات الافتراضية
    contract = ContractInputs(
        contract_duration=20,
        grace_period=2,
        rent_increase_interval=5,
        rent_increase_rate=10.0,
        capitalization_rate=7.0
    )
    
    property_data = PropertyInputs(
        land_area=10000.0,
        building_factor=2.5,
        building_ratio=60.0,
        construction_cost_per_sqm=2000.0,
        landscaping_cost_per_sqm=500.0,
        infrastructure_cost_per_sqm=3000.0,
        development_years=2
    )
    
    cost_ratios = CostRatios(
        design_cost_ratio=7.0,
        supervision_cost_ratio=5.0,
        contingency_cost_ratio=2.0
    )
    
    # إنشاء الحاسبة
    calculator = RealEstateCalculator(contract, property_data, cost_ratios)
    
    # حساب النتائج
    print("🏗️ حاسبة الإيجار العقاري - تحليل متقدم")
    print("=" * 50)
    
    # حساب تكاليف التطوير
    costs = calculator.calculate_development_costs()
    print(f"📊 تكاليف التطوير الإجمالية: {costs['total_development_cost']:,.0f} ريال")
    print(f"📐 المساحة القابلة للبناء: {costs['buildable_area']:,.0f} م²")
    print()
    
    # البحث عن الإيجار الأمثل
    results = calculator.find_optimal_rent()
    
    print("📈 النتائج المحسوبة:")
    print(f"💰 الإيجار السنوي الأمثل: {results['optimal_annual_rent']:,.0f} ريال")
    print(f"📊 صافي القيمة الحالية: {results['npv']:,.0f} ريال")
    print(f"⏱️ فترة الاسترداد: {results['payback_period']:.1f} سنة")
    print(f"📈 معدل العائد الداخلي: {results['irr']:.2f}%")
    print(f"💵 إجمالي العوائد: {results['total_returns']:,.0f} ريال")
    print(f"🔄 عدد التكرارات: {results['iterations']}")
    print()
    
    # عرض أول 5 سنوات من التدفقات النقدية
    print("💰 التدفقات النقدية (أول 5 سنوات):")
    print("-" * 80)
    print(f"{'السنة':<6} {'الإيجار السنوي':<15} {'التدفق المخصوم':<15} {'التدفق التراكمي':<15}")
    print("-" * 80)
    
    for cf in results['cash_flows'][:5]:
        print(f"{cf.year:<6} {cf.annual_rent:>14,.0f} {cf.discounted_cash_flow:>14,.0f} {cf.cumulative_cash_flow:>14,.0f}")
    
    # تصدير النتائج
    json_output = calculator.export_to_json()
    print(f"\n📄 تم تصدير النتائج إلى JSON (حجم: {len(json_output)} حرف)")


if __name__ == "__main__":
    main()

