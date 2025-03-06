from fastapi import FastAPI, UploadFile, File, Form
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from mlxtend.frequent_patterns import apriori
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
from fastapi.responses import JSONResponse

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
        return df
    except Exception as e:
        return JSONResponse(content={"error": f"File processing error: {str(e)}"}, status_code=400)

@app.post("/binning")
def binning(file: UploadFile = File(...), bins: int = Form(...)):
    df = process_file(file)
    if "Unit price" not in df.columns:
        return JSONResponse(content={"error": "Column 'Unit price' not found"}, status_code=400)
    
    df["binned"] = pd.cut(df["Unit price"], bins).astype(str)
    return df.to_dict(orient="records")

@app.post("/sampling")
def sampling(file: UploadFile = File(...), fraction: str = Form(...)):  # Accept as string for debugging
    print(f"Received fraction: {fraction}, type: {type(fraction)}")  # Debugging

    try:
        fraction = float(fraction)  # Convert to float
    except ValueError:
        return JSONResponse(content={"error": "Fraction must be a valid number"}, status_code=400)

    if not (0 < fraction <= 1):
        return JSONResponse(content={"error": "Fraction must be between 0 and 1"}, status_code=400)

    df = process_file(file)
    sample_df = df.sample(frac=fraction)
    return sample_df.to_dict(orient="records")

@app.post("/normalization")
def normalization(file: UploadFile = File(...)):
    df = process_file(file)

    numeric_cols = df.select_dtypes(include=[np.number])
    if numeric_cols.empty:
        return JSONResponse(content={"error": "No numeric columns found"}, status_code=400)

    scaler = MinMaxScaler()
    norm_df = pd.DataFrame(scaler.fit_transform(numeric_cols), columns=numeric_cols.columns)
    
    return norm_df.to_dict(orient="records")

@app.post("/pca")
async def pca(file: UploadFile = File(...), components: int = Form(...)):
    df = process_file(file)

    numeric_cols = df.select_dtypes(include=[np.number])
    if numeric_cols.shape[1] < components:
        return JSONResponse(content={"error": "Number of components exceeds available features"}, status_code=400)

    pca = PCA(n_components=components)
    transformed = pca.fit_transform(numeric_cols)
    return {
        "explained_variance_ratio": list(pca.explained_variance_ratio_),
        "components": transformed.tolist()
    }

@app.post("/histogram")
def histogram(file: UploadFile = File(...)):
    df = process_file(file)
    
    plt.figure()
    df.hist()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    
    return {"image": img_str}

@app.post("/scatterplot")
def scatterplot(file: UploadFile = File(...), x_col: str = Form(...), y_col: str = Form(...)):
    df = process_file(file)

    if x_col not in df.columns or y_col not in df.columns:
        return JSONResponse(content={"error": f"Columns '{x_col}' or '{y_col}' not found"}, status_code=400)

    plt.figure()
    sns.scatterplot(x=df[x_col], y=df[y_col])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")

    return {"image": img_str}

@app.post("/outliers")
async def detect_outliers(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)

    # Ensure numerical columns are used
    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.empty:
        return {"message": "No numerical data found for outlier detection."}

    # Compute Z-score and detect outliers
    z_scores = np.abs((numeric_df - numeric_df.mean()) / numeric_df.std())
    df_outliers = df[(z_scores > 2).any(axis=1)]

    # If no outliers found, return a message
    if df_outliers.empty:
        return {"message": "No outliers detected."}

    # Visualization
    plt.figure(figsize=(8, 6))
    x_col = numeric_df.columns[0]  # First numeric column as X
    y_col = numeric_df.columns[1] if numeric_df.shape[1] > 1 else x_col  # Second numeric column or duplicate X

    plt.scatter(numeric_df[x_col], numeric_df[y_col], color="blue", label="Normal Data", alpha=0.5)
    plt.scatter(df_outliers[x_col], df_outliers[y_col], color="red", label="Outliers", alpha=0.9)

    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.legend()
    plt.title("Outlier Detection Scatter Plot")

    # Convert plot to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")

    return {"image": img_str}




@app.post("/apriori")
def apriori_analysis(file: UploadFile = File(...), min_support: str = Form(...)):
    df = process_file(file)

    try:
        min_support = float(min_support)  # Convert min_support safely
    except ValueError:
        return JSONResponse(content={"error": "min_support must be a valid float"}, status_code=400)

    # Convert dataset into a format suitable for Apriori
    df = df.astype(str)  # Convert all columns to strings (ensures categorical)
    df = pd.get_dummies(df)  # One-hot encode the categorical values

    # Run Apriori
    frequent_itemsets = apriori(df, min_support=min_support, use_colnames=True)

    return frequent_itemsets.to_dict(orient="records")




@app.post("/clustering")
def clustering(file: UploadFile = File(...), clusters: int = Form(...)):
    df = process_file(file)

    numeric_cols = df.select_dtypes(include=[np.number])
    if numeric_cols.empty:
        return JSONResponse(content={"error": "No numeric columns found"}, status_code=400)

    kmeans = KMeans(n_clusters=clusters, n_init=10)
    df["Cluster"] = kmeans.fit_predict(numeric_cols)

    return df.to_dict(orient="records")
