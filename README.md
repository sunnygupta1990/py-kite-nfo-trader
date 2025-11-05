# Kite Connect NFO Trader

A comprehensive solution for NFO (Nifty Options and Futures) trading with Kite Connect API. This application provides a clean, modular architecture for fetching, analyzing, and managing NFO contracts.

## Features

- **Complete NFO Coverage**: Fetches contracts for all 209 stocks in the NFO list
- **Automatic Authentication**: Handles Kite Connect authentication seamlessly
- **Market Data Integration**: Real-time LTP, OHLC, volume, and change percentages
- **ATM/OTM Filtering**: Intelligent filtering of options based on ATM strikes
- **Interactive Menu**: User-friendly interface for various operations
- **Comprehensive Reporting**: Detailed contract summaries and coverage reports

## Project Structure

```
├── src/
│   └── kite_trader/
│       ├── core/           # Core application logic
│       │   ├── app.py      # Main application class
│       │   └── config.py   # Configuration management
│       ├── services/       # Business logic services
│       │   ├── auth_service.py      # Authentication handling
│       │   ├── nfo_service.py       # NFO contract operations
│       │   └── market_data_service.py # Market data operations
│       ├── ui/             # User interface
│       │   └── menu_service.py      # Menu and UI handling
│       └── utils/          # Utility functions
├── data/                   # Data files
│   └── Nfo_List.txt       # Complete NFO stocks list
├── tests/                  # Test files
├── logs/                   # Log files
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
└── setup.py               # Package setup
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd PyConnectAPI
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API credentials**:
   - Update `src/kite_trader/core/config.py` with your Kite Connect API credentials
   - Or use the interactive setup when running the application

## Usage

### Basic Usage

```bash
python main.py
```

### Interactive Menu

The application provides an interactive menu with the following options:

1. **Fetch Current Month NFO Contracts** - Main functionality
2. **View Account Information** - Account details and margins
3. **View Orders** - Order history
4. **View Positions** - Current positions
5. **View Holdings** - Portfolio holdings
6. **Get Market Quote** - Real-time quotes
7. **Search Instruments** - Search NFO instruments
8. **List Options Up 200%+** - Find high-performing options
9. **Refresh Session** - Renew authentication
10. **Exit** - Close application

### Key Features

#### Complete NFO Coverage
- Fetches contracts for all 209 stocks in the NFO list
- Provides 100% coverage instead of partial coverage
- Handles both futures and options contracts

#### Intelligent Contract Filtering
- Uses correct month format (25SEP) for contract detection
- Filters options to ATM and nearby strikes (configurable)
- Provides detailed coverage reports

#### Market Data Integration
- Real-time LTP (Last Traded Price)
- Complete OHLC data (Open, High, Low, Close)
- Volume and change percentage calculations
- Efficient batch processing for large datasets

## Configuration

### API Credentials

Update your API credentials in the configuration:

```python
# In src/kite_trader/core/config.py
api_key = "your_api_key"
api_secret = "your_api_secret"
```

### NFO List

The application uses `data/Nfo_List.txt` containing 209 NFO stocks. You can modify this list as needed.

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
flake8 src/
```

### Type Checking

```bash
mypy src/
```

## Architecture

The application follows clean architecture principles:

- **Separation of Concerns**: Each module has a single responsibility
- **Dependency Injection**: Services are injected rather than created internally
- **Interface Segregation**: Small, focused interfaces
- **Testability**: Each component can be tested independently

### Core Components

1. **KiteTraderApp**: Main application orchestrator
2. **AuthService**: Handles authentication and session management
3. **NFOService**: Manages NFO contract operations
4. **MarketDataService**: Handles market data fetching and processing
5. **MenuService**: Manages user interface and menu operations

## Troubleshooting

### Common Issues

1. **Authentication Failures**: Ensure API credentials are correct
2. **Missing Contracts**: Check if NFO list file exists and is readable
3. **API Limits**: The application handles API rate limits automatically

### Logs

Check the `logs/` directory for detailed error logs and debugging information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and informational purposes only. Trading involves risk, and past performance does not guarantee future results. Always do your own research and consider consulting with a financial advisor before making investment decisions.
