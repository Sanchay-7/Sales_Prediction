import { useState } from "react";
import axios from "axios";

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState(null);
  const [imageResponse, setImageResponse] = useState(null); // Store image separately
  const [operation, setOperation] = useState("binning");
  const [param, setParam] = useState(5);
  const [xCol, setXCol] = useState("");
  const [yCol, setYCol] = useState("");

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    // Attach parameters based on selected operation
    if (operation === "binning") {
      formData.append("bins", param);
    } else if (operation === "sampling") {
      formData.append("fraction", param);
    } else if (operation === "pca") {
      formData.append("components", param);
    } else if (operation === "apriori") {
      formData.append("min_support", param);
    } else if (operation === "clustering") {
      formData.append("clusters", param);
    } else if (operation === "scatterplot" || operation === "outliers") {
      formData.append("x_col", xCol);
      formData.append("y_col", yCol);
    }

    try {
      const res = await axios.post(`http://127.0.0.1:8000/${operation}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // Separate text and image response
      setResponse(res.data.text || res.data); // Store JSON/text response
      if (res.data.image) {
        setImageResponse(`data:image/png;base64,${res.data.image}`); // Store image separately
      } else {
        setImageResponse(null); // Reset image if no new image response
      }
    } catch (error) {
      console.error("Error:", error.response?.data || error.message);
      setResponse({ error: "An error occurred. Check the backend logs." });
      setImageResponse(null);
    }
  };

  return (
    <div className="p-5">
      <h1 className="text-2xl font-bold">Data Analysis App</h1>
      <form onSubmit={handleSubmit} className="mt-4 space-y-3">
        <input type="file" onChange={handleFileChange} className="border p-2" />

        <select onChange={(e) => setOperation(e.target.value)} className="border p-2">
          <option value="binning">Binning</option>
          <option value="sampling">Sampling</option>
          <option value="normalization">Normalization</option>
          <option value="pca">PCA</option>
          <option value="histogram">Histogram</option>
          <option value="scatterplot">Scatterplot</option>
          <option value="outliers">Outliers</option>
          <option value="apriori">Apriori</option>
          <option value="clustering">Clustering</option>
        </select>

        {/* Input for numerical parameters */}
        {["binning", "sampling", "pca", "apriori", "clustering"].includes(operation) && (
          <input
            type="number"
            value={param}
            onChange={(e) => setParam(e.target.value)}
            className="border p-2"
          />
        )}

        {/* Input for scatterplot & outliers columns */}
        {["scatterplot", "outliers"].includes(operation) && (
          <>
            <input
              type="text"
              placeholder="X Column"
              value={xCol}
              onChange={(e) => setXCol(e.target.value)}
              className="border p-2"
            />
            <input
              type="text"
              placeholder="Y Column"
              value={yCol}
              onChange={(e) => setYCol(e.target.value)}
              className="border p-2"
            />
          </>
        )}

        <button type="submit" className="bg-blue-500 text-white p-2">Analyze</button>
      </form>

      {/* Display Results */}
      {response && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold">Analysis Result:</h2>
          {typeof response === "string" ? (
            <p className="border p-2">{response}</p>
          ) : (
            <pre className="mt-4 p-2 border">{JSON.stringify(response, null, 2)}</pre>
          )}
        </div>
      )}

      {/* Display Image (if available) */}
      {imageResponse && (
        <div className="mt-4">
          <h2 className="text-xl font-semibold">Visualization:</h2>
          <img src={imageResponse} alt="Generated Visualization" className="border p-2 mt-2" />
        </div>
      )}
    </div>
  );
}

export default App;
