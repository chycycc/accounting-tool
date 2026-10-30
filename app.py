import json
import os
import re
import shutil
import uuid
from datetime import datetime
from io import BytesIO

from flask import Flask, jsonify, request, render_template, send_file
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data.json')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), 'backups')
BACKUP_KEEP = 20  # 自动备份保留份数


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"prices": [150, 180, 300], "records": {}, "extras_prices": [], "extras_records": {}}


def save_data(data):
    # 保存前自动备份当前版本，保留最近 BACKUP_KEEP 份
    if os.path.exists(DATA_FILE):
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            backup_path = os.path.join(BACKUP_DIR, f'data_{ts}.json')
            shutil.copy2(DATA_FILE, backup_path)
            backups = sorted(os.listdir(BACKUP_DIR))
            for old in backups[:-BACKUP_KEEP]:
                os.remove(os.path.join(BACKUP_DIR, old))
        except OSError:
            pass  # 备份失败不影响主流程
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_raw_input(raw_str):
    """Parse input like '750*5+422' or '670 800 670 670' or '183包' or '183b' into kg total."""
    raw_str = raw_str.strip().replace('×', '*').replace('x', '*').replace('X', '*')
    nums = []
    bag_kg = 0
    for part in re.split(r'[+]', raw_str):
        part = part.strip()
        if not part:
            continue
        # Handle 包 unit: 183包 or 183b => kg = 183/40*1000
        bag_match = re.match(r'^(\d+)\s*(包|b)$', part, re.IGNORECASE)
        if bag_match:
            bag_kg += round(int(bag_match.group(1)) / 40 * 1000)
            continue
        if '*' in part:
            nums_part = part.split('*')
            if len(nums_part) == 2:
                try:
                    val = int(nums_part[0].strip())
                    count = int(nums_part[1].strip())
                    nums.extend([val] * count)
                except ValueError:
                    pass
        else:
            for num in re.split(r'[\s,，]+', part):
                num = num.strip()
                if num:
                    try:
                        nums.append(int(num))
                    except ValueError:
                        pass
    return sum(nums) + bag_kg


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/prices', methods=['GET'])
def get_prices():
    data = load_data()
    return jsonify(data['prices'])


@app.route('/api/prices', methods=['POST'])
def add_price():
    data = load_data()
    price = request.json.get('price')
    if price and price not in data['prices']:
        data['prices'].append(price)
        data['prices'].sort()
        save_data(data)
    return jsonify(data['prices'])


@app.route('/api/prices/<int:price>', methods=['DELETE'])
def delete_price(price):
    data = load_data()
    if price in data['prices']:
        data['prices'].remove(price)
        save_data(data)
    return jsonify(data['prices'])


@app.route('/api/months', methods=['GET'])
def get_months():
    data = load_data()
    months = sorted(data['records'].keys(), reverse=True)
    return jsonify(months)


def date_sort_key(r):
    """按日期排序，如 7.1, 7.2, 7.10, 7.12"""
    parts = r['date'].split('.')
    return (int(parts[0]), int(parts[1])) if len(parts) == 2 else (0, 0)


@app.route('/api/records', methods=['GET'])
def get_records():
    month = request.args.get('month')
    data = load_data()
    records = data['records'].get(month, [])
    records.sort(key=date_sort_key)
    return jsonify(records)


@app.route('/api/records', methods=['POST'])
def add_record():
    data = load_data()
    req = request.json
    month = req.get('month')
    date = req.get('date')
    raw = req.get('raw')
    price = int(req.get('price'))

    kg = parse_raw_input(raw)
    if kg <= 0:
        return jsonify({'error': f'无法识别原始数据: {raw}'}), 400

    record = {
        'id': str(uuid.uuid4())[:8],
        'date': date,
        'raw': raw,
        'kg': kg,
        'price': price
    }

    if month not in data['records']:
        data['records'][month] = []
    data['records'][month].append(record)
    save_data(data)
    return jsonify(record), 201


@app.route('/api/records/<record_id>', methods=['DELETE'])
def delete_record(record_id):
    data = load_data()
    for month, records in data['records'].items():
        for i, r in enumerate(records):
            if r['id'] == record_id:
                records.pop(i)
                save_data(data)
                return jsonify({'ok': True})
    return jsonify({'error': 'not found'}), 404


@app.route('/api/records/<record_id>', methods=['PUT'])
def update_record(record_id):
    data = load_data()
    req = request.json
    raw = (req.get('raw') or '').strip()
    try:
        price = int(req.get('price'))
    except (TypeError, ValueError):
        return jsonify({'error': '单价无效'}), 400
    kg = parse_raw_input(raw)
    if kg <= 0:
        return jsonify({'error': f'无法识别原始数据: {raw}'}), 400
    for month, records in data['records'].items():
        for r in records:
            if r['id'] == record_id:
                r['raw'] = raw
                r['kg'] = kg
                r['price'] = price
                save_data(data)
                return jsonify(r)
    return jsonify({'error': 'not found'}), 404


@app.route('/api/report', methods=['GET'])
def get_report():
    year = request.args.get('year')
    data = load_data()
    report = {'months': [], 'by_price': {}}

    all_months = set(data['records'].keys()) | set(data.get('extras_records', {}).keys())
    for month_key in sorted(all_months):
        if year and not month_key.startswith(year):
            continue
        records = data['records'].get(month_key, [])
        total_kg = sum(r['kg'] for r in records)
        total_tons = total_kg / 1000
        total_amount = sum(r['kg'] / 1000 * r['price'] for r in records)
        extras = data.get('extras_records', {}).get(month_key, [])
        extra_kg = sum(r['kg'] for r in extras)
        extra_tons = extra_kg / 1000
        extra_amount = sum(r['kg'] / 1000 * r['price'] for r in extras)

        price_breakdown = {}
        for r in records:
            p = r['price']
            if p not in price_breakdown:
                price_breakdown[p] = {'kg': 0, 'amount': 0}
            price_breakdown[p]['kg'] += r['kg']
            price_breakdown[p]['amount'] += r['kg'] / 1000 * p

        report['months'].append({
            'month': month_key,
            'days': len(records),
            'total_kg': total_kg,
            'total_tons': round(total_tons, 3),
            'total_amount': round(total_amount, 2),
            'by_price': {str(k): v for k, v in price_breakdown.items()},
            'extra_days': len(extras),
            'extra_kg': extra_kg,
            'extra_tons': round(extra_tons, 3),
            'extra_amount': round(extra_amount, 2),
            'grand_amount': round(total_amount + extra_amount, 2)
        })

        for p, v in price_breakdown.items():
            if p not in report['by_price']:
                report['by_price'][p] = {'kg': 0, 'amount': 0}
            report['by_price'][p]['kg'] += v['kg']
            report['by_price'][p]['amount'] += v['amount']

    for p in report['by_price']:
        report['by_price'][p]['amount'] = round(report['by_price'][p]['amount'], 2)

    return jsonify(report)


@app.route('/api/top10', methods=['GET'])
def get_top10():
    year = request.args.get('year')
    data = load_data()
    all_records = []
    for month_key, records in data['records'].items():
        if year and not month_key.startswith(year):
            continue
        for r in records:
            all_records.append({**r, 'month': month_key})
    all_records.sort(key=lambda x: x['kg'], reverse=True)
    return jsonify(all_records[:10])


@app.route('/api/export', methods=['GET'])
def export_excel():
    month = request.args.get('month')
    data = load_data()
    records = sorted(data['records'].get(month, []), key=date_sort_key)
    extras = sorted(data.get('extras_records', {}).get(month, []), key=date_sort_key)

    wb = Workbook()
    ws = wb.active
    ws.title = f'{month}账目'

    header_font = Font(bold=True, size=12)
    blue_font = Font(size=11, color='0000FF')
    black_font = Font(size=11, color='000000')
    thin = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
    header_fill = PatternFill('solid', fgColor='D9E1F2')
    sum_fill = PatternFill('solid', fgColor='FFF2CC')
    center = Alignment(horizontal='center', vertical='center')

    headers = ['号期', '原始数据', '当号合计(kg)', '吨数', '单价(元/吨)', '金额(元)']
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.font = header_font
        c.fill = header_fill
        c.border = thin
        c.alignment = center

    widths = [10, 30, 16, 12, 14, 14]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w

    for i, r in enumerate(records, 2):
        ws.cell(row=i, column=1, value=r['date']).border = thin
        ws.cell(row=i, column=1).alignment = center
        ws.cell(row=i, column=2, value=r['raw']).border = thin
        ws.cell(row=i, column=3, value=r['kg']).font = blue_font
        ws.cell(row=i, column=3).border = thin
        ws.cell(row=i, column=3).alignment = center
        ws.cell(row=i, column=3).number_format = '#,##0'
        ws.cell(row=i, column=4, value=f'=C{i}/1000').font = black_font
        ws.cell(row=i, column=4).border = thin
        ws.cell(row=i, column=4).alignment = center
        ws.cell(row=i, column=4).number_format = '0.000'
        ws.cell(row=i, column=5, value=r['price']).font = blue_font
        ws.cell(row=i, column=5).border = thin
        ws.cell(row=i, column=5).alignment = center
        ws.cell(row=i, column=5).number_format = '#,##0'
        ws.cell(row=i, column=6, value=f'=D{i}*E{i}').font = black_font
        ws.cell(row=i, column=6).border = thin
        ws.cell(row=i, column=6).alignment = center
        ws.cell(row=i, column=6).number_format = '#,##0.00'

    lr = len(records) + 1
    sr = lr + 2
    labels = ['合计', '总天数', '总kg', '总吨', '总金额']
    for j, label in enumerate(labels):
        ws.merge_cells(start_row=sr+j, start_column=1, end_row=sr+j, end_column=2)
        for c in range(1, 3):
            ws.cell(row=sr+j, column=c).fill = sum_fill
            ws.cell(row=sr+j, column=c).border = thin
        ws.cell(row=sr+j, column=1, value=label).font = Font(bold=True, size=11)
        ws.cell(row=sr+j, column=1).alignment = center

    ws.cell(row=sr+1, column=3, value=f'=COUNTA(A2:A{lr})').font = black_font
    ws.cell(row=sr+1, column=3).fill = sum_fill
    ws.cell(row=sr+1, column=3).border = thin
    ws.cell(row=sr+1, column=3).alignment = center

    ws.cell(row=sr+2, column=3, value=f'=SUM(C2:C{lr})').font = black_font
    ws.cell(row=sr+2, column=3).fill = sum_fill
    ws.cell(row=sr+2, column=3).border = thin
    ws.cell(row=sr+2, column=3).alignment = center
    ws.cell(row=sr+2, column=3).number_format = '#,##0'

    ws.cell(row=sr+3, column=4, value=f'=SUM(D2:D{lr})').font = black_font
    ws.cell(row=sr+3, column=4).fill = sum_fill
    ws.cell(row=sr+3, column=4).border = thin
    ws.cell(row=sr+3, column=4).alignment = center
    ws.cell(row=sr+3, column=4).number_format = '0.000'

    ws.cell(row=sr+4, column=6, value=f'=SUM(F2:F{lr})').font = Font(bold=True, size=12, color='FF0000')
    ws.cell(row=sr+4, column=6).fill = sum_fill
    ws.cell(row=sr+4, column=6).border = thin
    ws.cell(row=sr+4, column=6).alignment = center
    ws.cell(row=sr+4, column=6).number_format = '#,##0.00'

    for j in range(5):
        for c in [3, 4, 5, 6]:
            ws.cell(row=sr+j, column=c).fill = sum_fill
            ws.cell(row=sr+j, column=c).border = thin

    # ===== 右侧并排：当月额外记录 =====
    if extras:
        extra_fill = PatternFill('solid', fgColor='E2EFDA')
        ex0 = 8  # H 列
        headers2 = ['号期', '原始数据', '当号合计(kg)', '吨数', '单价(元/吨)', '金额(元)']
        for j, h in enumerate(headers2):
            c = ws.cell(row=1, column=ex0+j, value=h)
            c.font = header_font
            c.fill = extra_fill
            c.border = thin
            c.alignment = center
        for i, r in enumerate(extras, 2):
            ws.cell(row=i, column=ex0, value=r['date']).border = thin
            ws.cell(row=i, column=ex0).alignment = center
            ws.cell(row=i, column=ex0+1, value=r['raw']).border = thin
            ws.cell(row=i, column=ex0+2, value=r['kg']).font = blue_font
            ws.cell(row=i, column=ex0+2).border = thin
            ws.cell(row=i, column=ex0+2).alignment = center
            ws.cell(row=i, column=ex0+2).number_format = '#,##0'
            ws.cell(row=i, column=ex0+3, value=f'=J{i}/1000').font = black_font
            ws.cell(row=i, column=ex0+3).border = thin
            ws.cell(row=i, column=ex0+3).alignment = center
            ws.cell(row=i, column=ex0+3).number_format = '0.000'
            ws.cell(row=i, column=ex0+4, value=r['price']).font = blue_font
            ws.cell(row=i, column=ex0+4).border = thin
            ws.cell(row=i, column=ex0+4).alignment = center
            ws.cell(row=i, column=ex0+4).number_format = '#,##0'
            ws.cell(row=i, column=ex0+5, value=f'=K{i}*L{i}').font = black_font
            ws.cell(row=i, column=ex0+5).border = thin
            ws.cell(row=i, column=ex0+5).alignment = center
            ws.cell(row=i, column=ex0+5).number_format = '#,##0.00'
        ex_lr = len(extras) + 1
        ex_sr = ex_lr + 2
        ws.column_dimensions['G'].width = 2
        for j, w in enumerate([10, 30, 16, 12, 14, 14]):
            ws.column_dimensions[chr(72 + j)].width = w
        labels2 = ['合计', '总天数', '总kg', '总吨', '总金额']
        for j, label in enumerate(labels2):
            ws.merge_cells(start_row=ex_sr+j, start_column=ex0, end_row=ex_sr+j, end_column=ex0+1)
            for c in range(ex0, ex0+2):
                ws.cell(row=ex_sr+j, column=c).fill = extra_fill
                ws.cell(row=ex_sr+j, column=c).border = thin
            ws.cell(row=ex_sr+j, column=ex0, value=label).font = Font(bold=True, size=11)
            ws.cell(row=ex_sr+j, column=ex0).alignment = center
        ws.cell(row=ex_sr+1, column=ex0+2, value=f'=COUNTA(H2:H{ex_lr})').fill = extra_fill
        ws.cell(row=ex_sr+1, column=ex0+2).border = thin
        ws.cell(row=ex_sr+1, column=ex0+2).alignment = center
        ws.cell(row=ex_sr+2, column=ex0+2, value=f'=SUM(J2:J{ex_lr})').fill = extra_fill
        ws.cell(row=ex_sr+2, column=ex0+2).border = thin
        ws.cell(row=ex_sr+2, column=ex0+2).alignment = center
        ws.cell(row=ex_sr+2, column=ex0+2).number_format = '#,##0'
        ws.cell(row=ex_sr+3, column=ex0+3, value=f'=SUM(K2:K{ex_lr})').fill = extra_fill
        ws.cell(row=ex_sr+3, column=ex0+3).border = thin
        ws.cell(row=ex_sr+3, column=ex0+3).alignment = center
        ws.cell(row=ex_sr+3, column=ex0+3).number_format = '0.000'
        ws.cell(row=ex_sr+4, column=ex0+5, value=f'=SUM(M2:M{ex_lr})').font = Font(bold=True, size=12, color='FF0000')
        ws.cell(row=ex_sr+4, column=ex0+5).fill = extra_fill
        ws.cell(row=ex_sr+4, column=ex0+5).border = thin
        ws.cell(row=ex_sr+4, column=ex0+5).alignment = center
        ws.cell(row=ex_sr+4, column=ex0+5).number_format = '#,##0.00'
        for j in range(5):
            for c in [ex0+2, ex0+3, ex0+4, ex0+5]:
                ws.cell(row=ex_sr+j, column=c).fill = extra_fill
                ws.cell(row=ex_sr+j, column=c).border = thin
        # 当月总计（主业+额外）
        gr = ex_sr + 6
        ws.merge_cells(start_row=gr, start_column=ex0, end_row=gr, end_column=ex0+1)
        ws.cell(row=gr, column=ex0, value='当月总计(主业+额外)').font = Font(bold=True, size=11)
        ws.cell(row=gr, column=ex0).fill = extra_fill
        ws.cell(row=gr, column=ex0).border = thin
        ws.cell(row=gr, column=ex0).alignment = center
        for c in [ex0+1, ex0+2, ex0+3, ex0+4]:
            ws.cell(row=gr, column=c).fill = extra_fill
            ws.cell(row=gr, column=c).border = thin
        ws.cell(row=gr, column=ex0+5, value=f'=F{sr+4}+M{ex_sr+4}').font = Font(bold=True, size=12, color='FF0000')
        ws.cell(row=gr, column=ex0+5).fill = extra_fill
        ws.cell(row=gr, column=ex0+5).border = thin
        ws.cell(row=gr, column=ex0+5).alignment = center
        ws.cell(row=gr, column=ex0+5).number_format = '#,##0.00'

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=f'{month}账目.xlsx')


@app.route('/api/export_report', methods=['GET'])
def export_report_excel():
    year = request.args.get('year')
    data = load_data()
    wb = Workbook()
    ws = wb.active
    ws.title = f'{year}年报表'

    header_font = Font(bold=True, size=12)
    black_font = Font(size=11, color='000000')
    thin = Border(left=Side('thin'), right=Side('thin'), top=Side('thin'), bottom=Side('thin'))
    header_fill = PatternFill('solid', fgColor='D9E1F2')
    sum_fill = PatternFill('solid', fgColor='FFF2CC')
    center = Alignment(horizontal='center', vertical='center')

    headers = ['月份', '天数', '总kg', '总吨', '主业金额(元)', '额外金额(元)', '当月合计(元)']
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=col, value=h)
        c.font = header_font
        c.fill = header_fill
        c.border = thin
        c.alignment = center

    widths = [12, 10, 14, 12, 16, 16, 16]
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w

    row_idx = 2
    months_data = []
    all_months = set(data['records'].keys()) | set(data.get('extras_records', {}).keys())
    for month_key in sorted(all_months):
        if year and not month_key.startswith(year):
            continue
        records = data['records'].get(month_key, [])
        extras = data.get('extras_records', {}).get(month_key, [])
        total_kg = sum(r['kg'] for r in records)
        total_tons = total_kg / 1000
        total_amount = sum(r['kg'] / 1000 * r['price'] for r in records)
        extra_kg = sum(r['kg'] for r in extras)
        extra_amount = sum(r['kg'] / 1000 * r['price'] for r in extras)
        months_data.append((month_key, len(records), total_kg, round(total_tons, 3), round(total_amount, 2), round(extra_amount, 2), round(total_amount + extra_amount, 2)))

    for md in months_data:
        for col, val in enumerate(md, 1):
            c = ws.cell(row=row_idx, column=col, value=val)
            c.font = black_font
            c.border = thin
            c.alignment = center
        ws.cell(row=row_idx, column=3).number_format = '#,##0'
        ws.cell(row=row_idx, column=4).number_format = '0.000'
        ws.cell(row=row_idx, column=5).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=6).number_format = '#,##0.00'
        ws.cell(row=row_idx, column=7).number_format = '#,##0.00'
        row_idx += 1

    sr = row_idx + 1
    ws.cell(row=sr, column=1, value='全年合计').font = Font(bold=True, size=11)
    ws.cell(row=sr, column=1).fill = sum_fill
    ws.cell(row=sr, column=1).border = thin
    ws.cell(row=sr, column=1).alignment = center
    ws.cell(row=sr, column=2, value=f'=SUM(B2:B{row_idx-1})').fill = sum_fill
    ws.cell(row=sr, column=2).border = thin
    ws.cell(row=sr, column=2).alignment = center
    ws.cell(row=sr, column=3, value=f'=SUM(C2:C{row_idx-1})').fill = sum_fill
    ws.cell(row=sr, column=3).border = thin
    ws.cell(row=sr, column=3).number_format = '#,##0'
    ws.cell(row=sr, column=3).alignment = center
    ws.cell(row=sr, column=4, value=f'=SUM(D2:D{row_idx-1})').fill = sum_fill
    ws.cell(row=sr, column=4).border = thin
    ws.cell(row=sr, column=4).number_format = '0.000'
    ws.cell(row=sr, column=4).alignment = center
    ws.cell(row=sr, column=5, value=f'=SUM(E2:E{row_idx-1})').fill = sum_fill
    ws.cell(row=sr, column=5).border = thin
    ws.cell(row=sr, column=5).number_format = '#,##0.00'
    ws.cell(row=sr, column=5).alignment = center
    ws.cell(row=sr, column=6, value=f'=SUM(F2:F{row_idx-1})').fill = sum_fill
    ws.cell(row=sr, column=6).border = thin
    ws.cell(row=sr, column=6).number_format = '#,##0.00'
    ws.cell(row=sr, column=6).alignment = center
    ws.cell(row=sr, column=7, value=f'=SUM(G2:G{row_idx-1})').fill = sum_fill
    ws.cell(row=sr, column=7).border = thin
    ws.cell(row=sr, column=7).number_format = '#,##0.00'
    ws.cell(row=sr, column=7).alignment = center
    ws.cell(row=sr, column=7).font = Font(bold=True, size=12, color='FF0000')

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=f'{year}年报表.xlsx')


# ===== 额外账本（与主业完全独立：额外单价 + 额外记录）=====

@app.route('/api/extras/prices', methods=['GET'])
def get_extras_prices():
    data = load_data()
    return jsonify(data.get('extras_prices', []))


@app.route('/api/extras/prices', methods=['POST'])
def add_extras_price():
    data = load_data()
    try:
        price = int(request.json.get('price'))
    except (TypeError, ValueError):
        return jsonify({'error': '单价无效'}), 400
    if price <= 0:
        return jsonify({'error': '单价必须大于 0'}), 400
    extras = data.setdefault('extras_prices', [])
    if price not in extras:
        extras.append(price)
        extras.sort()
        save_data(data)
    return jsonify(extras)


@app.route('/api/extras/prices/<int:price>', methods=['DELETE'])
def delete_extras_price(price):
    data = load_data()
    extras = data.setdefault('extras_prices', [])
    if price in extras:
        extras.remove(price)
        save_data(data)
    return jsonify(extras)


@app.route('/api/extras/months', methods=['GET'])
def get_extras_months():
    data = load_data()
    months = sorted(data.get('extras_records', {}).keys(), reverse=True)
    return jsonify(months)


@app.route('/api/extras/records', methods=['GET'])
def get_extras_records():
    month = request.args.get('month')
    data = load_data()
    records = data.get('extras_records', {}).get(month, [])
    records.sort(key=date_sort_key)
    return jsonify(records)


def make_extras_record(date, raw, price):
    kg = parse_raw_input(raw)
    if kg <= 0:
        return None
    return {'id': str(uuid.uuid4())[:8], 'date': date, 'raw': raw, 'kg': kg, 'price': price}


@app.route('/api/extras/records', methods=['POST'])
def add_extras_record():
    data = load_data()
    req = request.json
    month = req.get('month')
    date = (req.get('date') or '').strip()
    raw = (req.get('raw') or '').strip()
    try:
        price = int(req.get('price'))
    except (TypeError, ValueError):
        return jsonify({'error': '单价无效'}), 400
    rec = make_extras_record(date, raw, price)
    if rec is None:
        return jsonify({'error': f'无法识别原始数据: {raw}'}), 400
    extras = data.setdefault('extras_records', {})
    extras.setdefault(month, []).append(rec)
    save_data(data)
    return jsonify(rec), 201


@app.route('/api/extras/records/batch', methods=['POST'])
def add_extras_records_batch():
    data = load_data()
    req = request.json
    month = req.get('month')
    items = req.get('records') or []
    added = []
    skipped = []
    for it in items:
        date = (it.get('date') or '').strip()
        raw = (it.get('raw') or '').strip()
        try:
            price = int(it.get('price'))
        except (TypeError, ValueError):
            price = 0
        rec = make_extras_record(date, raw, price)
        if rec is None or not date:
            skipped.append({'date': date, 'raw': raw})
            continue
        added.append(rec)
    if added:
        extras = data.setdefault('extras_records', {})
        extras.setdefault(month, []).extend(added)
        save_data(data)
    return jsonify({'ok': True, 'added': len(added), 'skipped': len(skipped), 'skipped_items': skipped})


@app.route('/api/extras/records/<record_id>', methods=['PUT'])
def update_extras_record(record_id):
    data = load_data()
    req = request.json
    raw = (req.get('raw') or '').strip()
    try:
        price = int(req.get('price'))
    except (TypeError, ValueError):
        return jsonify({'error': '单价无效'}), 400
    kg = parse_raw_input(raw)
    if kg <= 0:
        return jsonify({'error': f'无法识别原始数据: {raw}'}), 400
    for records in data.get('extras_records', {}).values():
        for r in records:
            if r['id'] == record_id:
                r['raw'] = raw
                r['kg'] = kg
                r['price'] = price
                save_data(data)
                return jsonify(r)
    return jsonify({'error': 'not found'}), 404


@app.route('/api/extras/records/<record_id>', methods=['DELETE'])
def delete_extras_record(record_id):
    data = load_data()
    for records in data.get('extras_records', {}).values():
        for i, r in enumerate(records):
            if r['id'] == record_id:
                records.pop(i)
                save_data(data)
                return jsonify({'ok': True})
    return jsonify({'error': 'not found'}), 404


@app.route('/api/export_data', methods=['GET'])
def export_data():
    data = load_data()
    buf = BytesIO()
    buf.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='application/json', as_attachment=True,
                     download_name='账本数据备份.json')


@app.route('/api/import_data', methods=['POST'])
def import_data():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': '未选择文件'}), 400
    try:
        data = json.loads(f.read().decode('utf-8'))
    except Exception:
        return jsonify({'error': '文件不是有效的 JSON'}), 400
    if not isinstance(data, dict) or 'records' not in data or 'prices' not in data:
        return jsonify({'error': '数据格式不正确，请上传本工具的备份文件'}), 400
    data.setdefault('extras_prices', [])
    data.setdefault('extras_records', {})
    save_data(data)
    return jsonify({'ok': True, 'message': '导入成功'})


if __name__ == '__main__':
    # 默认开启调试，生产环境用环境变量 FLASK_DEBUG=0 关闭
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug)
