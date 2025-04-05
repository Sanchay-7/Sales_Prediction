import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [imageResponse, setImageResponse] = useState(null);
  const [operation, setOperation] = useState("sales_trends");
  const [param, setParam] = useState(5);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) return;
  
    const formData = new FormData();
    formData.append("file", file);
  
    if (operation === "clustering") {
      formData.append("clusters", param);
    } else if (operation === "apriori") {
      formData.append("min_support", param);
    }
  
    try {
      const res = await axios.post(`http://127.0.0.1:8000/${operation}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
  
      setResponse(res.data.clusters || res.data);
      setImageResponse(res.data.image ? `data:image/png;base64,${res.data.image}` : null);
    } catch (error) {
      console.error("Error:", error.response?.data || error.message);
      setResponse({ error: "An error occurred. Check the backend logs." });
      setImageResponse(null);
    }
  };
  

  return (
    <div className="min-h-screen bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 text-white flex flex-col items-center p-6">
      {/* Dashboard Card */}
      <div className="w-full max-w-3xl bg-white bg-opacity-10 backdrop-blur-md shadow-xl rounded-2xl p-6">
        <h1 className="text-3xl font-bold text-center mb-4 text-black">📊 E-Commerce Sales Analysis</h1>
        
        {/* Upload Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input 
            type="file" 
            onChange={handleFileChange} 
            className="w-full text-gray-300 bg-gray-800 border border-gray-600 p-2 rounded-lg focus:ring-2 focus:ring-blue-400"
          />

          {/* Dropdown */}
          <select 
            onChange={(e) => setOperation(e.target.value)} 
            className="w-full bg-gray-800 border border-gray-600 text-gray-300 p-2 rounded-lg"
          >
            <option value="sales_trends">📈 Sales Trends</option>
            <option value="clustering">🧑‍🤝‍🧑 Customer Segmentation</option>
            <option value="apriori">🛒 Market Basket Analysis</option>
            <option value="outliers">⚠️ Fraud Detection</option>
          </select>

          {/* Dynamic Input Field */}
          {operation === "clustering" || operation === "apriori" ? (
            <input 
              type="number" 
              value={param} 
              onChange={(e) => setParam(e.target.value)} 
              className="w-full bg-gray-800 border border-gray-600 text-gray-300 p-2 rounded-lg"
            />
          ) : null}

          {/* Submit Button */}
          <button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-500 transition-all p-3 text-lg font-semibold rounded-lg shadow-md"
          >
            🚀 Analyze Data
          </button>
        </form>

        {/* Analysis Result */}
        {response && (
          <div className="mt-6 bg-gray-800 p-4 rounded-lg shadow-lg">
            <h2 className="text-xl font-semibold text-black">📊 Analysis Result:</h2>
            <pre className="mt-3 p-3 bg-gray-900 text-gray-300 rounded-lg overflow-auto max-h-60">
              {JSON.stringify(response, null, 2)}
            </pre>
          </div>
        )}

        {/* Visualization Image */}
        {imageResponse && (
          <div className="mt-6 flex flex-col items-center">
            <h2 className="text-xl font-semibold text-black">📌 Visualization:</h2>
            <img src={imageResponse} alt="Generated Visualization" className="rounded-lg mt-3 shadow-md" />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
