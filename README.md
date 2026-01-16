# LOCKON IP Prism

LOCKON IP Prism is a sophisticated desktop application designed for **Threat Intelligence** and **SOC Analysts**. It provides bulk IP reputation checking by integrating with **IPQualityScore (IPQS)** and **AlienVault OTX**, wrapped in a modern, user-friendly GUI built with `CustomTkinter`.

## 🚀 Key Features

*   **Bulk IP Analysis**: Import `.txt` or `.log` files to analyze hundreds of IPs simultaneously.
*   **Dual Intelligence Sources**: 
    *   **IPQualityScore**: Fraud scores, bot detection, and high-risk IP identification.
    *   **AlienVault OTX**: Threat pulses and community-reported indicators.
*   **Smart Caching System**: Uses a local SQLite database (`ip_prism.db`) to cache results, saving API credits and speeding up re-analysis.
*   **Interactive Dashboard**: Real-time statistics including Total IPs analyzed, Top Malicious Countries, and Batch history.
*   **Advanced Reporting**:
    *   **Recurrence Reports**: Identify IPs that persistently appear across multiple scans.
    *   **Comparison Reports**: Analyze differences between two datasets.
    *   **PDF Exports**: Generate professional reports for stakeholders.
*   **Modern GUI**: Dark mode interface with responsive layout and progress tracking.

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Meow-011/LOCKON-IP-Prism.git
    cd LOCKON-IP-Prism
    ```

2.  **Set up a Virtual Environment (Recommended)**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

1.  Create a `.env` file in the root directory.
2.  Add your API keys (Get them from [IPQualityScore](https://www.ipqualityscore.com/) and [AlienVault OTX](https://otx.alienvault.com/)):

    ```env
    IPQS_API_KEY=your_ipqs_api_key_here
    OTX_API_KEY=your_otx_api_key_here
    CACHE_DURATION_HOURS=24
    ```

## 🖥️ Usage

1.  Run the application:
    ```bash
    python app.py
    ```
2.  **Dashboard**: View your overall stats.
3.  **Analysis**:
    *   Click **Select IP File** to load a list of IPs (one per line).
    *   Enter a description for the batch.
    *   Click **Start Analysis**.
4.  **View Reports**: Access detailed logs, recurrence data, and generate PDFs via the "View History & Reports" button.

## 📦 Dependencies

*   `customtkinter` - UI Framework
*   `aiohttp` - Async API requests
*   `requests` - Synchronous API requests
*   `python-dotenv` - Environment variable management
*   `matplotlib` - Data visualization
*   `reportlab` - PDF generation
*   `pyperclip` - Clipboard operations

## 👤 Author

**Meow-011**
*   GitHub: [Meow-011](https://github.com/Meow-011)

