# Instagram Epic Tool - Feature Overview

## Core Features Implemented

### 1. Instagram API Client (`instagram_client.py`)
- Secure authentication using Instagram credentials
- Fetch followers and following data
- Get user information by username
- Error handling with security-conscious logging

### 2. Network Analyzer (`analyzer.py`)
- **Unfollowers Detection**: Identify users you follow who don't follow back
- **Fans Analysis**: Find followers you don't follow back
- **Mutual Followers**: Identify mutual follow relationships
- **Summary Statistics**: Comprehensive overview of your network

### 3. Graph Visualizer (`visualizer.py`)
- Create directed graph representations of Instagram networks
- Color-coded nodes:
  - Red: You (central user)
  - Green: Mutual followers
  - Blue: Your followers
  - Yellow: People you follow
- Export visualizations as high-quality PNG images
- Graph statistics (nodes, edges, density)

### 4. CLI Interface (`main.py`)
Command-line interface with multiple options:
- `--visualize`: Create network graph
- `--analyze`: Show network statistics
- `--unfollowers`: List users who don't follow back
- `--fans`: List followers you don't follow back
- `--mutual`: List mutual followers
- `--save-data`: Export data to JSON files

### 5. Demo Mode (`demo.py`)
- Test the tool without Instagram credentials
- Generate example visualization
- Understand the tool's capabilities before use

### 6. Unit Tests (`test_instagram_tool.py`)
- 6 comprehensive test cases
- Tests for analyzer and visualizer components
- All tests passing

## Security Features

- Credentials stored in separate config file (excluded from version control)
- No logging of sensitive data
- Sanitized error messages to prevent credential leakage
- CodeQL security scan performed

## Dependencies

- `instagrapi==2.1.2`: Instagram API access
- `networkx==3.2.1`: Graph creation and analysis
- `matplotlib==3.8.2`: Visualization
- `python-dotenv==1.0.0`: Configuration management

All dependencies verified for security vulnerabilities.

## Usage Examples

### Basic Analysis
```bash
python main.py --analyze
```

### Full Network Visualization
```bash
python main.py --visualize --analyze --unfollowers --fans --mutual
```

### Export All Data
```bash
python main.py --analyze --save-data --visualize
```

## Output Files

- `instagram_network.png`: Network visualization
- `followers.json`: All followers data
- `following.json`: All following data
- `unfollowers.json`: Users who don't follow back
- `fans.json`: Followers you don't follow back
- `mutual_followers.json`: Mutual connections

## Testing

Run unit tests:
```bash
python -m unittest test_instagram_tool.py -v
```

Run demo:
```bash
python demo.py
```
