from fastapi import FastAPI, UploadFile, File, Form
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import matplotlib
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from mlxtend.frequent_patterns import apriori, association_rules
from fastapi import HTTPException
matplotlib.use('Agg')  # Use a non-GUI backend

app = FastAPI()

# Allow frontend (Vite.js) requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Helper function to process uploaded files
def process_file(file: UploadFile):
    try:
        df = pd.read_csv(file.file)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")  # Convert Date column
        return df
    except Exception as e:
        return JSONResponse(content={"error": f"File processing error: {str(e)}"}, status_code=400)

@app.post("/sales_trends")
def sales_trends(file: UploadFile = File(...)):
    df = process_file(file)
    
    if df is None or df.empty:
        return JSONResponse(content={"error": "File processing failed or dataset is empty"}, status_code=400)
    
    # Ensure the Date column is properly parsed
    if "Date" not in df.columns or df["Date"].isnull().all():
        return JSONResponse(content={"error": "Invalid or missing Date column"}, status_code=400)
    
    df.sort_values("Date", inplace=True)  # Sort by date
    sales_trend = df.groupby("Date")["Weekly_Sales"].sum()
    
    # Plot sales trends
    plt.figure(figsize=(10, 5))
    plt.plot(sales_trend.index, sales_trend.values, marker='o', linestyle='-')
    plt.xlabel("Date")
    plt.ylabel("Total Sales")
    plt.title("Sales Trends Over Time")
    plt.grid()
    
    # Convert plot to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    
    return {"image": img_str}

@app.post("/clustering")
def clustering(file: UploadFile = File(...), clusters: int = Form(...)):
    df = process_file(file)
    
    # Select only numeric columns for clustering
    numeric_cols = df.select_dtypes(include=[np.number])
    if numeric_cols.shape[1] < 2:
        return JSONResponse(content={"error": "At least two numeric columns are required for clustering visualization."}, status_code=400)
    
    # Standardize the data for better clustering results
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(numeric_cols)

    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=clusters, n_init=10, random_state=42)
    df["Cluster"] = kmeans.fit_predict(scaled_data)

    # Scatter plot for visualization (using the first two numeric columns)
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x=numeric_cols.iloc[:, 0], y=numeric_cols.iloc[:, 1], hue=df["Cluster"], palette="viridis", alpha=0.7)
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], color="red", marker="X", s=200, label="Centroids")
    plt.xlabel(numeric_cols.columns[0])
    plt.ylabel(numeric_cols.columns[1])
    plt.legend()
    plt.title("K-Means Clustering")

    # Convert plot to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")

    return {
        "image": img_str,
        "clusters": df.to_dict(orient="records")
    }


@app.post("/apriori")
def apriori_analysis(file: UploadFile = File(...), min_support: float = Form(...)):
    try:
        df = process_file(file)

        # Check if dataset is loaded properly
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="File processing failed or dataset is empty.")

        # Ensure necessary columns exist
        required_columns = ["Transaction_ID", "Item"]
        for col in required_columns:
            if col not in df.columns:
                raise HTTPException(status_code=400, detail=f"Missing required column: {col}")

        # Convert data to a transaction format
        basket = df.groupby("Transaction_ID")["Item"].apply(list).reset_index()

        # Convert transaction lists into binary matrix format (One-hot encoding)
        transaction_list = basket["Item"].tolist()
        unique_items = set(item for sublist in transaction_list for item in sublist)

        encoded_basket = pd.DataFrame([{item: (item in transaction) for item in unique_items} for transaction in transaction_list])

        # Apply Apriori algorithm
        frequent_itemsets = apriori(encoded_basket, min_support=min_support, use_colnames=True)

        # Check if any frequent itemsets were found
        if frequent_itemsets.empty:
            raise HTTPException(status_code=400, detail="No frequent itemsets found. Try lowering min_support.")

        # Generate association rules
        rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)

        return {
            "frequent_itemsets": frequent_itemsets.to_dict(orient="records"),
            "rules": rules.to_dict(orient="records"),
        }
    
    except Exception as e:
        print(f"Error in /apriori: {str(e)}")  # Print error in backend logs
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/outliers")
def detect_outliers(file: UploadFile = File(...)):
    df = process_file(file)
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return JSONResponse(content={"message": "No numerical data found for outlier detection."}, status_code=400)
    
    z_scores = np.abs((numeric_df - numeric_df.mean()) / numeric_df.std())
    df_outliers = df[(z_scores > 2).any(axis=1)]
    if df_outliers.empty:
        return {"message": "No outliers detected."}
    
    x_col = numeric_df.columns[0]
    y_col = numeric_df.columns[1] if numeric_df.shape[1] > 1 else x_col
    plt.figure(figsize=(8, 6))
    plt.scatter(numeric_df[x_col], numeric_df[y_col], color="blue", label="Normal Data", alpha=0.5)
    plt.scatter(df_outliers[x_col], df_outliers[y_col], color="red", label="Outliers", alpha=0.9)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.legend()
    plt.title("Outlier Detection Scatter Plot")
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    
    return {"image": img_str}
