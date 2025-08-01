from flask import Flask, render_template, request, jsonify
import json
import math
from datetime import datetime

app = Flask(__name__)

app.jinja_env.globals['format'] = format

def load_stock_data():
    """Load stock data from results.json file"""
    try:
        with open('results.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("results.json file not found!")
        return {}
    except json.JSONDecodeError:
        print("Error decoding JSON file!")
        return {}

def count_fulfilled_criteria(stock_data):
    """Count how many criteria are fulfilled for a stock"""
    criteria = ['dividend', 'pe', 'roe', 'leverage', 'volume']
    fulfilled_count = 0
    
    for criterion in criteria:
        if criterion in stock_data and stock_data[criterion].get('fulfilled', False):
            fulfilled_count += 1
    
    return fulfilled_count

def process_stock_data(stocks_data):
    """Process stock data to include fulfilled criteria count"""
    processed_stocks = []
    
    for symbol, data in stocks_data.items():
        stock_info = {
            'symbol': symbol,
            'name': data.get('name', 'N/A'),
            'industry': data.get('industry', 'N/A'),
            'market_cap': data.get('market_cap', 0),
            'fulfilled_criteria': count_fulfilled_criteria(data),
            'criteria_details': {
                'dividend': data.get('dividend', {}).get('fulfilled', False),
                'pe': data.get('pe', {}).get('fulfilled', False),
                'roe': data.get('roe', {}).get('fulfilled', False),
                'leverage': data.get('leverage', {}).get('fulfilled', False),
                'volume': data.get('volume', {}).get('fulfilled', False)
            }
        }
        processed_stocks.append(stock_info)
    
    return processed_stocks

@app.route('/')
def index():
    """Main page with stock listings and pagination"""
    # Load and process stock data
    stocks_data = load_stock_data()
    processed_stocks = process_stock_data(stocks_data)
    
    # Get sorting parameters
    sort_by = request.args.get('sort', 'criteria')  # criteria, symbol, name, industry, market_cap
    sort_order = request.args.get('order', 'desc')  # asc, desc
    
    # Sort the data
    if sort_by == 'criteria':
        processed_stocks.sort(key=lambda x: x['fulfilled_criteria'], reverse=(sort_order == 'desc'))
    elif sort_by == 'symbol':
        processed_stocks.sort(key=lambda x: x['symbol'], reverse=(sort_order == 'desc'))
    elif sort_by == 'name':
        processed_stocks.sort(key=lambda x: x['name'], reverse=(sort_order == 'desc'))
    elif sort_by == 'industry':
        processed_stocks.sort(key=lambda x: x['industry'], reverse=(sort_order == 'desc'))
    elif sort_by == 'market_cap':
        processed_stocks.sort(key=lambda x: x['market_cap'], reverse=(sort_order == 'desc'))
    else:
        # Default sorting: by criteria (desc) then by symbol (asc)
        processed_stocks.sort(key=lambda x: (-x['fulfilled_criteria'], x['symbol']))
    
    # Pagination parameters - increase default per_page for table format
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # Increased from 20 to 50
    
    # Validate per_page
    if per_page not in [25, 50, 100]:
        per_page = 50
    
    # Calculate pagination
    total_stocks = len(processed_stocks)
    total_pages = math.ceil(total_stocks / per_page)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_stocks = processed_stocks[start_idx:end_idx]
    
    # Calculate pagination info
    pagination_info = {
        'current_page': page,
        'total_pages': total_pages,
        'total_stocks': total_stocks,
        'per_page': per_page,
        'start_idx': start_idx + 1,
        'end_idx': min(end_idx, total_stocks),
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }
    
    # Sorting info for template
    sort_info = {
        'current_sort': sort_by,
        'current_order': sort_order,
        'opposite_order': 'asc' if sort_order == 'desc' else 'desc'
    }
    
    return render_template('index.html', 
                         stocks=paginated_stocks, 
                         pagination=pagination_info,
                         sort_info=sort_info)

@app.route('/api/stock/<symbol>')
def get_stock_details(symbol):
    """API endpoint to get detailed information about a specific stock"""
    stocks_data = load_stock_data()
    
    if symbol not in stocks_data:
        return jsonify({'error': 'Stock not found'}), 404
    
    stock_data = stocks_data[symbol]
    
    # Process the detailed data
    detailed_info = {
        'symbol': symbol,
        'name': stock_data.get('name', 'N/A'),
        'industry': stock_data.get('industry', 'N/A'),
        'market_cap': stock_data.get('market_cap', 0),
        'fulfilled_criteria': count_fulfilled_criteria(stock_data),
        'criteria': {
            'dividend': {
                'fulfilled': stock_data.get('dividend', {}).get('fulfilled', False),
                'values': stock_data.get('dividend', {}).get('value', {})
            },
            'pe': {
                'fulfilled': stock_data.get('pe', {}).get('fulfilled', False),
                'values': stock_data.get('pe', {}).get('value', {})
            },
            'roe': {
                'fulfilled': stock_data.get('roe', {}).get('fulfilled', False),
                'values': stock_data.get('roe', {}).get('value', {})
            },
            'leverage': {
                'fulfilled': stock_data.get('leverage', {}).get('fulfilled', False),
                'values': stock_data.get('leverage', {}).get('value', {})
            },
            'volume': {
                'fulfilled': stock_data.get('volume', {}).get('fulfilled', False),
                'values': stock_data.get('volume', {}).get('value', {})
            }
        }
    }
    
    return jsonify(detailed_info)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    """Detail page for a specific stock"""
    stocks_data = load_stock_data()
    
    if symbol not in stocks_data:
        return render_template('404.html'), 404
    
    stock_data = stocks_data[symbol]
    
    # Process the detailed data
    detailed_info = {
        'symbol': symbol,
        'name': stock_data.get('name', 'N/A'),
        'industry': stock_data.get('industry', 'N/A'),
        'market_cap': stock_data.get('market_cap', 0),
        'fulfilled_criteria': count_fulfilled_criteria(stock_data),
        'criteria': {
            'dividend': {
                'fulfilled': stock_data.get('dividend', {}).get('fulfilled', False),
                'data': stock_data.get('dividend', {}).get('value', {})
            },
            'pe': {
                'fulfilled': stock_data.get('pe', {}).get('fulfilled', False),
                'data': stock_data.get('pe', {}).get('value', {})
            },
            'roe': {
                'fulfilled': stock_data.get('roe', {}).get('fulfilled', False),
                'data': stock_data.get('roe', {}).get('value', {})
            },
            'leverage': {
                'fulfilled': stock_data.get('leverage', {}).get('fulfilled', False),
                'data': stock_data.get('leverage', {}).get('value', {})
            },
            'volume': {
                'fulfilled': stock_data.get('volume', {}).get('fulfilled', False),
                'data': stock_data.get('volume', {}).get('value', {})
            }
        }
    }

    print(json.dumps(detailed_info, indent=4, ensure_ascii=False))
    
    return render_template('stock_detail.html', stock=detailed_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)