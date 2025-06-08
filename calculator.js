// حاسبة الإيجار العقاري - JavaScript
// تحويل الأرقام إلى العربية
function toArabicNumbers(num) {
    const arabicNums = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    return num.toString().replace(/[0-9]/g, function(w) {
        return arabicNums[+w];
    });
}

// تنسيق الأرقام مع الفواصل والأرقام العربية
function formatArabicNumber(num) {
    if (isNaN(num) || num === null || num === undefined) return '٠';
    return toArabicNumbers(Math.round(num).toLocaleString('en-US'));
}

// تنسيق الأرقام العشرية
function formatArabicDecimal(num, decimals = 2) {
    if (isNaN(num) || num === null || num === undefined) return '٠.٠';
    return toArabicNumbers(num.toFixed(decimals));
}

// الحصول على قيم المدخلات
function getInputValues() {
    return {
        contractDuration: parseFloat(document.getElementById('contractDuration').value) || 20,
        gracePeriod: parseFloat(document.getElementById('gracePeriod').value) || 2,
        rentIncreaseInterval: parseFloat(document.getElementById('rentIncreaseInterval').value) || 5,
        rentIncreaseRate: parseFloat(document.getElementById('rentIncreaseRate').value) || 10,
        capitalizationRate: parseFloat(document.getElementById('capitalizationRate').value) || 7,
        landArea: parseFloat(document.getElementById('landArea').value) || 10000,
        buildingFactor: parseFloat(document.getElementById('buildingFactor').value) || 2.5,
        constructionCost: parseFloat(document.getElementById('constructionCost').value) || 2000,
        totalDevelopmentCost: parseFloat(document.getElementById('totalDevelopmentCost').value) || 93480000
    };
}

// حساب صافي القيمة الحالية
function calculateNPV(annualRent, inputs) {
    let cashFlowData = [];
    let currentRent = annualRent;
    let npv = -inputs.totalDevelopmentCost;
    let cumulativeCashFlow = -inputs.totalDevelopmentCost;

    for (let year = 1; year <= inputs.contractDuration; year++) {
        let yearlyRent = 0;
        
        // تطبيق منطق بدء الإيجار بعد فترة السماح
        if (year > inputs.gracePeriod) {
            yearlyRent = currentRent;
            
            // تطبيق الزيادات الدورية
            if (year > inputs.gracePeriod && 
                (year - inputs.gracePeriod - 1) % inputs.rentIncreaseInterval === 0 && 
                year > inputs.gracePeriod + 1) {
                currentRent *= (1 + inputs.rentIncreaseRate / 100);
                yearlyRent = currentRent;
            }
        }

        // حساب التدفق المخصوم
        const discountedCashFlow = yearlyRent / Math.pow(1 + inputs.capitalizationRate / 100, year);
        npv += discountedCashFlow;
        cumulativeCashFlow += discountedCashFlow;

        cashFlowData.push({
            year: year,
            rent: yearlyRent,
            discountedCashFlow: discountedCashFlow,
            cumulativeCashFlow: cumulativeCashFlow
        });
    }

    return { npv, cashFlowData };
}

// البحث عن أعلى إيجار مربح باستخدام البحث الثنائي
function findOptimalRent(inputs) {
    let low = 0;
    let high = 50000000; // 50 مليون كحد أقصى
    let optimalRent = 0;
    let iterations = 0;
    const maxIterations = 50;

    while (high - low > 1000 && iterations < maxIterations) {
        const mid = Math.floor((low + high) / 2);
        const { npv } = calculateNPV(mid, inputs);
        
        if (npv >= 0) {
            optimalRent = mid;
            low = mid;
        } else {
            high = mid;
        }
        iterations++;
    }

    return optimalRent;
}

// حساب فترة الاسترداد
function calculatePaybackPeriod(cashFlowData) {
    for (let i = 0; i < cashFlowData.length; i++) {
        if (cashFlowData[i].cumulativeCashFlow >= 0) {
            return i + 1;
        }
    }
    return cashFlowData.length;
}

// حساب معدل العائد السنوي
function calculateAnnualReturn(optimalRent, totalDevelopmentCost) {
    if (totalDevelopmentCost === 0) return 0;
    return (optimalRent / totalDevelopmentCost) * 100;
}

// تحديث عرض النتائج
function updateResults(optimalRent, npv, paybackPeriod, annualReturn) {
    document.getElementById('optimalRent').textContent = formatArabicNumber(optimalRent) + ' ريال';
    
    const npvElement = document.getElementById('npvValue');
    npvElement.textContent = formatArabicNumber(npv) + ' ريال';
    npvElement.className = 'result-value arabic-number ' + (npv >= 0 ? 'positive' : 'negative');
    
    document.getElementById('paybackPeriod').textContent = formatArabicNumber(paybackPeriod) + ' سنة';
    document.getElementById('annualReturn').textContent = formatArabicDecimal(annualReturn) + '%';
}

// تحديث جدول التدفقات النقدية
function updateCashFlowTable(cashFlowData) {
    const tbody = document.getElementById('cashFlowBody');
    tbody.innerHTML = '';

    cashFlowData.forEach(flow => {
        const row = tbody.insertRow();
        
        // السنة
        const yearCell = row.insertCell(0);
        yearCell.textContent = toArabicNumbers(flow.year);
        
        // الإيجار السنوي
        const rentCell = row.insertCell(1);
        rentCell.textContent = flow.rent > 0 ? formatArabicNumber(flow.rent) : '-';
        
        // التدفق المخصوم
        const discountedCell = row.insertCell(2);
        discountedCell.textContent = formatArabicNumber(flow.discountedCashFlow);
        discountedCell.style.color = flow.discountedCashFlow >= 0 ? '#28a745' : '#dc3545';
        
        // التدفق التراكمي
        const cumulativeCell = row.insertCell(3);
        cumulativeCell.textContent = formatArabicNumber(flow.cumulativeCashFlow);
        cumulativeCell.style.color = flow.cumulativeCashFlow >= 0 ? '#28a745' : '#dc3545';
    });
}

// تحديث المزلاج التفاعلي
function updateSlider(maxValue) {
    const slider = document.getElementById('rentSlider');
    slider.max = maxValue * 1.5; // 150% من القيمة المثلى كحد أقصى
    slider.value = maxValue;
    
    document.getElementById('maxRentValue').textContent = formatArabicNumber(maxValue * 1.5);
    document.getElementById('currentRentValue').textContent = formatArabicNumber(maxValue);
}

// تحديث قيمة المزلاج التفاعلي
function updateRentValue() {
    const slider = document.getElementById('rentSlider');
    const currentValue = parseFloat(slider.value);
    const inputs = getInputValues();
    
    document.getElementById('currentRentValue').textContent = formatArabicNumber(currentValue);
    
    // حساب NPV للقيمة المختارة
    const { npv } = calculateNPV(currentValue, inputs);
    const npvElement = document.getElementById('interactiveNPV');
    npvElement.textContent = formatArabicNumber(npv) + ' ريال';
    npvElement.className = 'result-value arabic-number ' + (npv >= 0 ? 'positive' : 'negative');
}

// الدالة الرئيسية لحساب النتائج
function calculateOptimalRent() {
    try {
        // الحصول على المدخلات
        const inputs = getInputValues();
        
        // التحقق من صحة المدخلات
        if (inputs.totalDevelopmentCost <= 0) {
            alert('يرجى إدخال قيمة صحيحة لتكاليف التطوير');
            return;
        }
        
        if (inputs.contractDuration <= 0) {
            alert('يرجى إدخال مدة عقد صحيحة');
            return;
        }
        
        // البحث عن الإيجار الأمثل
        const optimalRent = findOptimalRent(inputs);
        
        // حساب النتائج التفصيلية
        const { npv, cashFlowData } = calculateNPV(optimalRent, inputs);
        const paybackPeriod = calculatePaybackPeriod(cashFlowData);
        const annualReturn = calculateAnnualReturn(optimalRent, inputs.totalDevelopmentCost);
        
        // تحديث العرض
        updateResults(optimalRent, npv, paybackPeriod, annualReturn);
        updateCashFlowTable(cashFlowData);
        updateSlider(optimalRent);
        
        // تحديث NPV التفاعلي
        updateRentValue();
        
        console.log('تم حساب النتائج بنجاح:', {
            optimalRent,
            npv,
            paybackPeriod,
            annualReturn
        });
        
    } catch (error) {
        console.error('خطأ في الحسابات:', error);
        alert('حدث خطأ في الحسابات. يرجى التحقق من المدخلات والمحاولة مرة أخرى.');
    }
}

// تحديث تلقائي عند تغيير المدخلات
document.addEventListener('DOMContentLoaded', function() {
    // إضافة مستمعات الأحداث لجميع المدخلات
    const inputs = document.querySelectorAll('input[type="number"]');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            // تأخير قصير لتجنب الحسابات المتكررة
            clearTimeout(this.timeout);
            this.timeout = setTimeout(calculateOptimalRent, 500);
        });
    });
    
    // حساب أولي
    calculateOptimalRent();
});

// دالة لتصدير النتائج (اختيارية)
function exportResults() {
    const inputs = getInputValues();
    const optimalRent = findOptimalRent(inputs);
    const { npv, cashFlowData } = calculateNPV(optimalRent, inputs);
    
    const results = {
        inputs: inputs,
        results: {
            optimalRent: optimalRent,
            npv: npv,
            paybackPeriod: calculatePaybackPeriod(cashFlowData),
            annualReturn: calculateAnnualReturn(optimalRent, inputs.totalDevelopmentCost)
        },
        cashFlowData: cashFlowData,
        timestamp: new Date().toISOString()
    };
    
    // تحويل إلى JSON وتحميل
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'real-estate-calculation-results.json';
    link.click();
    
    URL.revokeObjectURL(url);
}

// إضافة دالة للطباعة
function printResults() {
    window.print();
}

