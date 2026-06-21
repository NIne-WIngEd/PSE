"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type UploadItem = {
  item_id: string;
  item_index: number;
  item_dir: string;
  saved_path: string;
  saved_filename: string;
  original_filename: string;
  mask_path: string;
  mask_filename: string;
  predicted_class: string;
  confidence: number;
  probabilities: Record<string, number>;
  cnn_model_name: string;
  unet_model_name: string;
  original_image_url: string;
  mask_image_url: string;
  job_id?: string;
  job_dir?: string;
};

type UploadBatchResponse = {
  message: string;
  client_session_id: string;
  job_id: string;
  job_dir: string;
  batch_count: number;
  cnn_model_name: string;
  unet_model_name: string;
  items: UploadItem[];
};

type MetricRow = {
  key: string;
  label: string;
  value: string;
};

type AnalysisResponse = {
  message: string;
  summary: string;
  job_id: string;
  job_dir: string;
  item_id: string;
  cnn_model_name: string;
  unet_model_name: string;
  predicted_class: string;
  confidence: number;
  probabilities: Record<string, number>;
  final_mask_path: string;
  final_mask_filename: string;
  original_filename: string;
  original_image_url: string;
  final_mask_url: string;
  extra1_url: string;
  extra2_url: string;
  extra3_url: string;
  extra4_url: string;
  extra1_note: string;
  extra2_note: string;
  extra3_note: string;
  extra4_note: string;
  metrics: MetricRow[];
  details: string;
  additional_outputs?: { label: string; url: string }[];
};

const BACKEND_URL = "http://127.0.0.1:8050";
const CANVAS_SIZE = 520;

function getOrCreateClientSessionId() {
  if (typeof window === "undefined") return "";
  const key = "afm_client_session_id";
  const existing = window.localStorage.getItem(key);
  if (existing) return existing;

  const created =
    "sess_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
  window.localStorage.setItem(key, created);
  return created;
}

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isDrawingRef = useRef(false);
  const hiddenFileInputRef = useRef<HTMLInputElement | null>(null);

  const [clientSessionId, setClientSessionId] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [batchData, setBatchData] = useState<UploadBatchResponse | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string>("");
  const [analysisMap, setAnalysisMap] = useState<Record<string, AnalysisResponse>>(
    {}
  );
  const [editedMaskMap, setEditedMaskMap] = useState<Record<string, string>>({});

  const [status, setStatus] = useState(
    "SYSTEM READY — Upload one or more AFM images to begin."
  );
  const [activeTab, setActiveTab] = useState<"upload" | "results">("upload");
  const [toolMode, setToolMode] = useState<"draw" | "erase">("draw");
  const [brushSize, setBrushSize] = useState(10);
  const [maskMode, setMaskMode] = useState<"use" | "edit">("edit");
  const [strokeCount, setStrokeCount] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    setClientSessionId(getOrCreateClientSessionId());
  }, []);

  const currentItem = useMemo(() => {
    if (!batchData?.items?.length) return null;
    return batchData.items.find((item) => item.item_id === selectedItemId) || batchData.items[0];
  }, [batchData, selectedItemId]);

  const currentAnalysis = useMemo(() => {
    if (!currentItem) return null;
    return analysisMap[currentItem.item_id] || null;
  }, [analysisMap, currentItem]);

  const sortedProbabilities = useMemo(() => {
    if (!currentItem?.probabilities) return [];
    return Object.entries(currentItem.probabilities).sort((a, b) => b[1] - a[1]);
  }, [currentItem]);

  const currentStep = Object.keys(analysisMap).length > 0 ? 3 : currentItem ? 2 : 1;

  const getCanvasContext = () => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    return canvas.getContext("2d");
  };

  const getCanvasDataUrl = () => {
    const canvas = canvasRef.current;
    if (!canvas) return "";
    return canvas.toDataURL("image/png");
  };

  const loadMaskToCanvas = (src: string) => {
    const canvas = canvasRef.current;
    const ctx = getCanvasContext();
    if (!canvas || !ctx) return;

    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
    img.src = src;
  };

  const saveCurrentCanvasForItem = (itemId?: string) => {
    if (!itemId || !canvasRef.current) return;
    if (maskMode !== "edit") return;

    const dataUrl = getCanvasDataUrl();
    if (!dataUrl) return;

    setEditedMaskMap((prev) => ({
      ...prev,
      [itemId]: dataUrl,
    }));
  };

  useEffect(() => {
    if (!currentItem?.item_id) return;

    const editedVersion = editedMaskMap[currentItem.item_id];
    if (editedVersion) {
      loadMaskToCanvas(editedVersion);
    } else if (currentItem.mask_image_url) {
      loadMaskToCanvas(currentItem.mask_image_url);
    }

    setStrokeCount(0);
    setMaskMode("edit");
  }, [currentItem?.item_id, editedMaskMap, currentItem?.mask_image_url]);

  const getCanvasPoint = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (canvas.width / rect.width),
      y: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  };

  const beginPathAt = (x: number, y: number) => {
    const ctx = getCanvasContext();
    if (!ctx) return;
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const drawDot = (x: number, y: number) => {
    const ctx = getCanvasContext();
    if (!ctx) return;

    ctx.beginPath();
    ctx.fillStyle = toolMode === "draw" ? "white" : "black";
    ctx.arc(x, y, Math.max(brushSize / 2, 1), 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (maskMode !== "edit") return;
    isDrawingRef.current = true;
    const point = getCanvasPoint(e);
    if (!point) return;
    beginPathAt(point.x, point.y);
    drawDot(point.x, point.y);
    setStrokeCount((prev) => prev + 1);
  };

  const stopDrawing = () => {
    isDrawingRef.current = false;
    const ctx = getCanvasContext();
    ctx?.beginPath();

    if (currentItem?.item_id && maskMode === "edit") {
      const dataUrl = getCanvasDataUrl();
      if (dataUrl) {
        setEditedMaskMap((prev) => ({
          ...prev,
          [currentItem.item_id]: dataUrl,
        }));
      }
    }
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawingRef.current || maskMode !== "edit") return;

    const canvas = canvasRef.current;
    const ctx = getCanvasContext();
    const point = getCanvasPoint(e);

    if (!canvas || !ctx || !point) return;

    ctx.lineWidth = brushSize;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = toolMode === "draw" ? "white" : "black";

    ctx.lineTo(point.x, point.y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(point.x, point.y);
  };

  const resetMask = () => {
    if (currentItem?.mask_image_url) {
      loadMaskToCanvas(currentItem.mask_image_url);
      setEditedMaskMap((prev) => {
        const next = { ...prev };
        delete next[currentItem.item_id];
        return next;
      });
      setStrokeCount(0);
      setStatus("MASK RESET — Restored original U-Net mask preview.");
    }
  };

  const handleNewJob = () => {
    setSelectedFiles([]);
    setBatchData(null);
    setSelectedItemId("");
    setAnalysisMap({});
    setEditedMaskMap({});
    setStatus("SYSTEM READY — Upload one or more AFM images to begin.");
    setToolMode("draw");
    setBrushSize(10);
    setMaskMode("edit");
    setStrokeCount(0);
    setActiveTab("upload");
    const ctx = getCanvasContext();
    ctx?.clearRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);
    if (hiddenFileInputRef.current) hiddenFileInputRef.current.value = "";
  };

  const handleUpload = async () => {
    if (!selectedFiles.length) {
      setStatus("ERROR — Please choose one or more files first.");
      return;
    }

    setAnalysisMap({});
    setEditedMaskMap({});
    setIsUploading(true);
    setStatus("PROCESSING — Uploading batch and running CNN + U-Net on each image...");

    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append("files", file));
    formData.append("client_session_id", clientSessionId);

    try {
      const res = await fetch(`${BACKEND_URL}/api/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        setStatus(`ERROR — ${data.error || "Upload failed"}`);
        return;
      }

      setBatchData(data);
      if (data.items?.length) {
        setSelectedItemId(data.items[0].item_id);
      }

      setStatus(
        `UPLOAD COMPLETE — Job ${data.job_id} created with ${data.batch_count} image${data.batch_count === 1 ? "" : "s"}.`
      );
      setActiveTab("upload");
    } catch (error) {
      setStatus("ERROR — Failed to connect to backend.");
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunAnalysis = async () => {
    if (!batchData?.items?.length) {
      setStatus("ERROR — Upload a batch first.");
      return;
    }

    let editedMasksSnapshot = { ...editedMaskMap };

    if (currentItem?.item_id && maskMode === "edit" && canvasRef.current) {
      const dataUrl = getCanvasDataUrl();
      if (dataUrl) {
        editedMasksSnapshot[currentItem.item_id] = dataUrl;
        setEditedMaskMap(editedMasksSnapshot);
      }
    }

    setIsRunning(true);
    setStatus(
      `ANALYSIS RUNNING — Executing analysis for all ${batchData.items.length} images in this batch...`
    );

    try {
      const payload = {
        job_id: batchData.job_id,
        job_dir: batchData.job_dir,
        items: batchData.items,
        edited_masks_by_item_id: editedMasksSnapshot,
      };

      const res = await fetch(`${BACKEND_URL}/api/run-analysis-batch`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        setStatus(`ERROR — ${data.error || "Batch analysis failed"}`);
        return;
      }

      const nextMap: Record<string, AnalysisResponse> = {};
      for (const result of data.results || []) {
        nextMap[result.item_id] = result;
      }

      setAnalysisMap(nextMap);
      setActiveTab("results");
      setStatus(
        `COMPLETE — Batch analysis finished for ${data.result_count || 0} image${
          data.result_count === 1 ? "" : "s"
        }.`
      );
    } catch (error) {
      setStatus("ERROR — Failed to connect to backend.");
      console.error(error);
    } finally {
      setIsRunning(false);
    }
  };

  const handleExportCurrentPdf = async () => {
    if (!batchData || !currentItem || !currentAnalysis) {
      setStatus("ERROR — No analyzed item available to export.");
      return;
    }

    setIsExporting(true);
    setStatus("EXPORTING — Building PDF for selected image...");

    try {
      const res = await fetch(`${BACKEND_URL}/api/export-pdf`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          batch_data: batchData,
          current_item: currentItem,
          current_analysis: currentAnalysis,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setStatus(`ERROR — ${data.error || "PDF export failed"}`);
        return;
      }

      const blob = await res.blob();
      const filename =
        `${(currentAnalysis.original_filename || "afm_result").replace(/\.[^.]+$/, "")}_analysis.pdf`;

      downloadBlob(blob, filename);
      setStatus("EXPORT COMPLETE — Selected result PDF downloaded.");
    } catch (error) {
      console.error(error);
      setStatus("ERROR — Failed to export selected PDF.");
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportBatchPdf = async () => {
    if (!batchData?.items?.length) {
      setStatus("ERROR — No batch available to export.");
      return;
    }

    const analysisResults = Object.values(analysisMap);
    if (!analysisResults.length) {
      setStatus("ERROR — Run analysis before exporting batch PDF.");
      return;
    }

    setIsExporting(true);
    setStatus("EXPORTING — Building batch PDF...");

    try {
      const res = await fetch(`${BACKEND_URL}/api/export-pdf-batch`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          batch_data: batchData,
          items: batchData.items,
          analysis_results: analysisResults,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setStatus(`ERROR — ${data.error || "Batch PDF export failed"}`);
        return;
      }

      const blob = await res.blob();
      const filename = `afm_batch_${batchData.job_id}.pdf`;

      downloadBlob(blob, filename);
      setStatus("EXPORT COMPLETE — Batch PDF downloaded.");
    } catch (error) {
      console.error(error);
      setStatus("ERROR — Failed to export batch PDF.");
    } finally {
      setIsExporting(false);
    }
  };

  const badgeClass = (name?: string) => String(name || "unknown").toUpperCase();

  const renderProbabilityBars = () => {
    if (!sortedProbabilities.length) {
      return (
        <div style={{ color: "var(--muted)", fontSize: "0.72rem" }}>
          Waiting for classification results.
        </div>
      );
    }

    const topLabel = sortedProbabilities[0][0];

    return sortedProbabilities.map(([label, value]) => {
      const pct = Math.max(0, Math.min(100, value * 100));
      const isTop = label === topLabel;

      return (
        <div className="prob-row" key={label}>
          <span className="prob-lbl">{label}</span>
          <div className="prob-track">
            <div
              className={`prob-fill ${isTop ? "top" : ""}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="prob-val">{pct.toFixed(1)}%</span>
        </div>
      );
    });
  };

  return (
    <>
      <style jsx global>{`
        :root {
          --bg: #0a0e17;
          --surface: #111827;
          --surface2: #1a2236;
          --border: #1e2d45;
          --accent: #00d4ff;
          --accent2: #7c3aed;
          --green: #00ff9d;
          --yellow: #ffd60a;
          --text: #e2e8f0;
          --muted: #4a6280;
        }

        * {
          box-sizing: border-box;
        }

        html, body {
          margin: 0;
          padding: 0;
          background: var(--bg);
          color: var(--text);
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }

        body::before {
          content: "";
          position: fixed;
          inset: 0;
          z-index: 9999;
          pointer-events: none;
          background: repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(0, 0, 0, 0.04) 2px,
            rgba(0, 0, 0, 0.04) 4px
          );
        }

        button,
        input,
        select {
          font: inherit;
        }

        .prob-row {
          display: grid;
          grid-template-columns: 72px 1fr 62px;
          gap: 8px;
          align-items: center;
          margin-bottom: 8px;
        }

        .prob-lbl {
          font-size: 0.7rem;
          color: var(--muted);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .prob-track {
          height: 10px;
          border-radius: 999px;
          overflow: hidden;
          background: var(--surface2);
          border: 1px solid var(--border);
        }

        .prob-fill {
          height: 100%;
          background: rgba(0, 212, 255, 0.45);
        }

        .prob-fill.top {
          background: linear-gradient(90deg, var(--accent), var(--accent2));
        }

        .prob-val {
          font-size: 0.72rem;
          color: var(--accent);
          text-align: right;
          font-weight: 700;
        }
      `}</style>

      <main style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text)" }}>
        <nav
          style={{
            background: "var(--surface)",
            borderBottom: "1px solid var(--border)",
            padding: "0 32px",
            height: 52,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 100,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: "var(--accent)",
                boxShadow: "0 0 12px rgba(0,212,255,0.7)",
              }}
            />
            <div style={{ fontWeight: 800, letterSpacing: "0.05em", fontSize: "1.1rem" }}>
              AFM Analysis
            </div>
            <span
              style={{
                fontSize: "0.62rem",
                color: "var(--muted)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                alignSelf: "flex-end",
                marginBottom: 2,
              }}
            >
              // nanoscale imaging
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <span
              style={{
                fontSize: "0.68rem",
                color: "var(--muted)",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "var(--green)",
                  boxShadow: "0 0 10px rgba(0,255,157,0.8)",
                  display: "inline-block",
                }}
              />
              SYSTEM ONLINE
            </span>

            <button
              onClick={handleNewJob}
              style={{
                background: "transparent",
                border: "1px solid var(--border)",
                color: "var(--muted)",
                padding: "5px 12px",
                borderRadius: 4,
                fontSize: "0.73rem",
                cursor: "pointer",
              }}
            >
              ⟳ New Job
            </button>
          </div>
        </nav>

        <div
          style={{
            background: "var(--surface)",
            borderBottom: "1px solid var(--border)",
            padding: "10px 32px",
            display: "flex",
            alignItems: "center",
          }}
        >
          <Step
            label="Upload & Detect"
            number="01"
            state={currentStep > 1 ? "done" : currentStep === 1 ? "active" : "idle"}
          />
          <StepLine done={currentStep > 1} />
          <Step
            label="Review Mask"
            number="02"
            state={currentStep > 2 ? "done" : currentStep === 2 ? "active" : "idle"}
          />
          <StepLine done={currentStep > 2} />
          <Step
            label="Analysis"
            number="03"
            state={currentStep === 3 ? "active" : "idle"}
          />
        </div>

        <div style={{ maxWidth: 1280, margin: "0 auto", padding: "24px 28px" }}>
          <div style={{ display: "flex", gap: 6, marginBottom: 22 }}>
            <button
              onClick={() => setActiveTab("upload")}
              style={tabButtonStyle(activeTab === "upload")}
            >
              ▶ Stage: Upload & Edit
            </button>
            <button
              onClick={() => setActiveTab("results")}
              style={tabButtonStyle(activeTab === "results")}
            >
              ▶ Stage: Results
            </button>
          </div>

          {activeTab === "upload" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.35fr", gap: 18 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <Panel title="Input Batch">
                  <div
                    onClick={() => hiddenFileInputRef.current?.click()}
                    style={{
                      border: "1px dashed var(--border)",
                      borderRadius: 6,
                      padding: "36px 24px",
                      textAlign: "center",
                      cursor: "pointer",
                      background: "rgba(0,212,255,0.02)",
                    }}
                  >
                    <input
                      ref={hiddenFileInputRef}
                      type="file"
                      accept=".jpg,.jpeg,.png,.tif,.tiff"
                      multiple
                      onChange={(e) => {
                        const files = Array.from(e.target.files || []);
                        setSelectedFiles(files);
                      }}
                      style={{ display: "none" }}
                    />
                    <div style={{ fontSize: "2.4rem", color: "var(--accent)", opacity: 0.8 }}>
                      ⤴
                    </div>
                    <div style={{ fontSize: "1rem", fontWeight: 700, letterSpacing: "0.05em" }}>
                      {selectedFiles.length
                        ? `${selectedFiles.length} file${selectedFiles.length === 1 ? "" : "s"} selected`
                        : "Drop AFM Images Here"}
                    </div>
                    <div style={{ fontSize: "0.73rem", color: "var(--muted)", marginTop: 4 }}>
                      {selectedFiles.length
                        ? "Batch ready — click upload below"
                        : "or click to browse multiple files"}
                    </div>
                  </div>

                  {!!selectedFiles.length && (
                    <div style={{ marginTop: 12 }}>
                      <div style={smallLabelStyle}>Selected Files</div>
                      <div
                        style={{
                          maxHeight: 180,
                          overflowY: "auto",
                          border: "1px solid var(--border)",
                          borderRadius: 6,
                          background: "var(--surface2)",
                        }}
                      >
                        {selectedFiles.map((file, idx) => (
                          <div
                            key={`${file.name}-${idx}`}
                            style={{
                              padding: "8px 10px",
                              borderBottom:
                                idx === selectedFiles.length - 1 ? "none" : "1px solid var(--border)",
                              fontSize: "0.74rem",
                              color: "var(--text)",
                            }}
                          >
                            {idx + 1}. {file.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div style={{ marginTop: 14, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <button onClick={handleUpload} disabled={isUploading} style={runButtonStyle}>
                      {isUploading ? "Running..." : "Upload Batch"}
                    </button>
                    <span style={{ fontSize: "0.73rem", color: "var(--muted)" }}>
                      // one job id for the whole batch
                    </span>
                  </div>

                  {batchData && (
                    <div style={{ marginTop: 12, fontSize: "0.72rem", color: "var(--muted)" }}>
                      Job ID: <span style={{ color: "var(--accent)" }}>{batchData.job_id}</span>
                      {" · "}
                      Batch Count: <span style={{ color: "var(--accent)" }}>{batchData.batch_count}</span>
                    </div>
                  )}
                </Panel>

                <Panel title="Batch Items">
                  {batchData?.items?.length ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {batchData.items.map((item) => {
                        const isSelected = item.item_id === currentItem?.item_id;
                        const isDone = !!analysisMap[item.item_id];
                        const isEdited = !!editedMaskMap[item.item_id];

                        return (
                          <button
                            key={item.item_id}
                            onClick={() => {
                              saveCurrentCanvasForItem(currentItem?.item_id);
                              setSelectedItemId(item.item_id);
                              setActiveTab("upload");
                            }}
                            style={{
                              textAlign: "left",
                              padding: "10px 12px",
                              borderRadius: 6,
                              border: isSelected
                                ? "1px solid var(--accent)"
                                : "1px solid var(--border)",
                              background: isSelected
                                ? "rgba(0,212,255,0.08)"
                                : "var(--surface2)",
                              color: "var(--text)",
                              cursor: "pointer",
                            }}
                          >
                            <div style={{ fontSize: "0.76rem", fontWeight: 700 }}>
                              {item.item_index}. {item.original_filename}
                            </div>
                            <div style={{ fontSize: "0.68rem", color: "var(--muted)", marginTop: 4 }}>
                              Class: {badgeClass(item.predicted_class)} · Confidence:{" "}
                              {(item.confidence * 100).toFixed(1)}% ·{" "}
                              {isDone ? "Analysis complete" : isEdited ? "Edited mask saved" : "Pending analysis"}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ color: "var(--muted)", fontSize: "0.74rem" }}>
                      No batch uploaded yet.
                    </div>
                  )}
                </Panel>

                <Panel title="CNN Classification">
                  <div style={{ display: "flex", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "4px 12px",
                        borderRadius: 4,
                        fontSize: "0.78rem",
                        fontWeight: 700,
                        letterSpacing: "0.1em",
                        background: "rgba(0,212,255,0.1)",
                        color: "var(--accent)",
                        border: "1px solid rgba(0,212,255,0.3)",
                      }}
                    >
                      CPU {currentItem ? badgeClass(currentItem.predicted_class) : "WAITING"}
                    </span>

                    <span style={{ fontSize: "0.75rem", color: "var(--muted)" }}>
                      {currentItem
                        ? `${(currentItem.confidence * 100).toFixed(1)}% confidence`
                        : "No prediction yet"}
                    </span>
                  </div>

                  <div>{renderProbabilityBars()}</div>

                  <div style={{ marginTop: 16 }}>
                    <div style={smallLabelStyle}>Original Image</div>
                    <ImageFrame
                      src={currentItem?.original_image_url || ""}
                      caption={currentItem?.saved_filename || "No image loaded"}
                      height={240}
                    />
                  </div>
                </Panel>
              </div>

              <div>
                <Panel title="U-Net Segmentation Mask" style={{ marginBottom: 16 }}>
                  <p
                    style={{
                      fontSize: "0.76rem",
                      color: "var(--muted)",
                      lineHeight: 1.65,
                      marginBottom: 14,
                    }}
                  >
                    Automatic segmentation complete.{" "}
                    <span style={{ color: "var(--text)" }}>White regions</span> = detected features.{" "}
                    <span style={{ color: "var(--text)" }}>Black</span> = background.
                    Verify the mask for the selected batch item.
                  </p>

                  <ImageFrame
                    src={currentItem?.mask_image_url || ""}
                    caption={currentItem?.mask_filename || "unet_mask_preview.png"}
                    height={260}
                  />

                  <div style={{ marginTop: 14 }}>
                    <p
                      style={{
                        fontSize: "0.76rem",
                        fontWeight: 600,
                        color: "var(--text)",
                        marginBottom: 8,
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                      }}
                    >
                      Proceed with selected mask?
                    </p>

                    <RadioOption
                      active={maskMode === "use"}
                      accent="green"
                      onClick={() => setMaskMode("use")}
                      label="Use mask as-is"
                      icon="▶"
                    />
                    <RadioOption
                      active={maskMode === "edit"}
                      accent="accent"
                      onClick={() => setMaskMode("edit")}
                      label="Open editor to correct the mask"
                      icon="✎"
                    />
                  </div>
                </Panel>

                <Panel title="Mask Editor" accentColor="var(--accent2)">
                  <div style={{ display: "flex", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.72rem", color: "var(--muted)" }}>
                      <div style={{ width: 14, height: 14, borderRadius: 2, border: "1px solid #555", background: "#fff" }} />
                      White = draw features
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.72rem", color: "var(--muted)" }}>
                      <div style={{ width: 14, height: 14, borderRadius: 2, border: "1px solid var(--accent)", background: "#111" }} />
                      Black = erase features
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center", flexWrap: "wrap" }}>
                    <button onClick={() => setToolMode("draw")} style={toolButtonStyle(toolMode === "draw")}>
                      Brush Draw (white)
                    </button>

                    <button onClick={() => setToolMode("erase")} style={toolButtonStyle(toolMode === "erase")}>
                      Erase (black)
                    </button>

                    <button onClick={resetMask} style={secondaryButtonStyle}>
                      Reset Mask
                    </button>

                    <div
                      style={{
                        flex: 1,
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        marginLeft: 10,
                        minWidth: 220,
                      }}
                    >
                      <span style={{ fontSize: "0.68rem", color: "var(--muted)", whiteSpace: "nowrap" }}>
                        Brush px:
                      </span>
                      <input
                        type="range"
                        min={2}
                        max={40}
                        value={brushSize}
                        onChange={(e) => setBrushSize(Number(e.target.value))}
                        style={{ flex: 1, accentColor: "#00d4ff" }}
                      />
                      <span style={{ fontSize: "0.68rem", color: "var(--accent)", minWidth: 24 }}>
                        {brushSize}
                      </span>
                    </div>
                  </div>

                  <div
                    style={{
                      width: "100%",
                      minHeight: 300,
                      background: "#050810",
                      border: "1px solid var(--border)",
                      borderRadius: 4,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      position: "relative",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        inset: 0,
                        backgroundImage:
                          "linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px)",
                        backgroundSize: "24px 24px",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        width: 1,
                        height: "100%",
                        background: "rgba(0,212,255,0.1)",
                        left: "50%",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        width: "100%",
                        height: 1,
                        background: "rgba(0,212,255,0.1)",
                        top: "50%",
                      }}
                    />

                    <div style={{ position: "relative", zIndex: 1, padding: 12 }}>
                      <div
                        style={{
                          border: "1px solid var(--border)",
                          borderRadius: 4,
                          overflow: "hidden",
                          background: "#000",
                          boxShadow: "0 0 20px rgba(0,212,255,0.08)",
                        }}
                      >
                        <canvas
                          ref={canvasRef}
                          width={CANVAS_SIZE}
                          height={CANVAS_SIZE}
                          onMouseDown={startDrawing}
                          onMouseUp={stopDrawing}
                          onMouseLeave={stopDrawing}
                          onMouseMove={draw}
                          style={{
                            display: "block",
                            width: "100%",
                            maxWidth: 520,
                            height: "auto",
                            cursor: maskMode === "edit" ? "crosshair" : "not-allowed",
                            pointerEvents: currentItem && maskMode === "edit" ? "auto" : "none",
                            background: "#000",
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <p style={{ fontSize: "0.68rem", color: "var(--muted)", marginTop: 8 }}>
                    ↳ {strokeCount} stroke{strokeCount === 1 ? "" : "s"} recorded for current image.
                    {currentItem?.item_id && editedMaskMap[currentItem.item_id]
                      ? " Edited mask saved for batch run."
                      : ""}
                  </p>
                </Panel>

                <div style={{ display: "flex", alignItems: "center", padding: "16px 0", flexWrap: "wrap", gap: 10 }}>
                  <button
                    onClick={handleRunAnalysis}
                    disabled={isRunning || !batchData?.items?.length}
                    style={runButtonStyle}
                  >
                    {isRunning ? "Running..." : "Execute Full Batch"}
                  </button>
                  <span style={{ fontSize: "0.73rem", color: "var(--muted)" }}>
                    // one click analyzes every image in this batch
                  </span>
                </div>

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "10px 14px",
                    borderRadius: 4,
                    fontSize: "0.78rem",
                    border: "1px solid rgba(0,212,255,0.25)",
                    background: "rgba(0,212,255,0.06)",
                    color: "var(--accent)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  <span>●</span>
                  <span>{status}</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === "results" && (
            <div>
              <Panel title="Batch Results Navigator" style={{ marginBottom: 18 }}>
                {batchData?.items?.length ? (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 10 }}>
                    {batchData.items.map((item) => {
                      const isSelected = item.item_id === currentItem?.item_id;
                      const isDone = !!analysisMap[item.item_id];
                      return (
                        <button
                          key={item.item_id}
                          onClick={() => setSelectedItemId(item.item_id)}
                          style={{
                            textAlign: "left",
                            padding: "10px 12px",
                            borderRadius: 6,
                            border: isSelected
                              ? "1px solid var(--accent)"
                              : "1px solid var(--border)",
                            background: isSelected
                              ? "rgba(0,212,255,0.08)"
                              : "var(--surface2)",
                            color: "var(--text)",
                            cursor: "pointer",
                          }}
                        >
                          <div style={{ fontSize: "0.76rem", fontWeight: 700 }}>
                            {item.original_filename}
                          </div>
                          <div style={{ fontSize: "0.68rem", color: "var(--muted)", marginTop: 4 }}>
                            {badgeClass(item.predicted_class)} ·{" "}
                            {isDone ? "Analyzed" : "Not analyzed yet"}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ color: "var(--muted)", fontSize: "0.74rem" }}>
                    No batch available.
                  </div>
                )}
              </Panel>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "10px 14px",
                  borderRadius: 4,
                  fontSize: "0.78rem",
                  border: "1px solid rgba(0,255,157,0.25)",
                  background: "rgba(0,255,157,0.06)",
                  color: "var(--green)",
                  marginBottom: 18,
                }}
              >
                <span>✔</span>
                <span>
                  {currentAnalysis
                    ? `ANALYSIS COMPLETE — ${currentAnalysis.summary}`
                    : "No analysis result yet for the selected image."}
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  flexWrap: "wrap",
                  background: "var(--surface)",
                  border: "1px solid rgba(0,212,255,0.2)",
                  borderRadius: 6,
                  padding: "12px 18px",
                  marginBottom: 18,
                }}
              >
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "4px 12px",
                    borderRadius: 4,
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    letterSpacing: "0.1em",
                    background: "rgba(0,212,255,0.1)",
                    color: "var(--accent)",
                    border: "1px solid rgba(0,212,255,0.3)",
                  }}
                >
                  {currentItem ? badgeClass(currentItem.predicted_class) : "WAITING"}
                </span>

                <span style={{ fontSize: "0.76rem", color: "var(--muted)" }}>
                  {currentItem
                    ? `${(currentItem.confidence * 100).toFixed(1)}% confidence · ${currentItem.cnn_model_name} · ${currentItem.unet_model_name}`
                    : "Select an image"}
                </span>
              </div>

              <Panel title="Image Outputs" style={{ marginBottom: 18 }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
                    gap: 14,
                  }}
                >
                  <ResultsImage
                    label="Original"
                    src={currentAnalysis?.original_image_url || currentItem?.original_image_url || ""}
                    caption={currentAnalysis?.original_filename || currentItem?.saved_filename || "sample"}
                  />
                  <ResultsImage
                    label="Final Mask"
                    src={currentAnalysis?.final_mask_url || ""}
                    caption={currentAnalysis?.final_mask_filename || "unet_mask_final.png"}
                  />
                  <ResultsImage
                    label={currentAnalysis?.extra1_note || "Extra Output 1"}
                    src={currentAnalysis?.extra1_url || ""}
                    caption={currentAnalysis?.extra1_note || "extra_output_1.png"}
                  />
                  <ResultsImage
                    label={currentAnalysis?.extra2_note || "Extra Output 2"}
                    src={currentAnalysis?.extra2_url || ""}
                    caption={currentAnalysis?.extra2_note || "extra_output_2.png"}
                  />
                  <ResultsImage
                    label={currentAnalysis?.extra3_note || "Extra Output 3"}
                    src={currentAnalysis?.extra3_url || ""}
                    caption={currentAnalysis?.extra3_note || "extra_output_3.png"}
                  />
                  <ResultsImage
                    label={currentAnalysis?.extra4_note || "Extra Output 4"}
                    src={currentAnalysis?.extra4_url || ""}
                    caption={currentAnalysis?.extra4_note || "extra_output_4.png"}
                  />

                  {currentAnalysis?.additional_outputs?.map((img, idx) => (
                    <ResultsImage
                      key={`${img.label}-${idx}`}
                      label={img.label}
                      src={img.url}
                      caption={img.label}
                    />
                  ))}
                </div>
              </Panel>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 16,
                  marginBottom: 18,
                }}
              >
                <Panel title="Analysis Metrics">
                  {currentAnalysis?.metrics?.length ? (
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.76rem" }}>
                      <tbody>
                        {currentAnalysis.metrics.map((metric) => (
                          <tr key={metric.key} style={{ borderBottom: "1px solid var(--border)" }}>
                            <td
                              style={{
                                padding: "7px 0",
                                color: "var(--muted)",
                                textTransform: "uppercase",
                                fontSize: "0.68rem",
                                letterSpacing: "0.06em",
                              }}
                            >
                              {metric.label}
                            </td>
                            <td
                              style={{
                                padding: "7px 0",
                                color: "var(--accent)",
                                fontWeight: 700,
                                textAlign: "right",
                              }}
                            >
                              {metric.value}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ color: "var(--muted)", fontSize: "0.76rem" }}>
                      No analysis has been run yet for the selected image.
                    </div>
                  )}
                </Panel>

                <Panel title="Job Details" accentColor="var(--muted)">
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.76rem" }}>
                    <tbody>
                      <JobRow label="CNN model" value={currentItem?.cnn_model_name || "-"} />
                      <JobRow label="U-Net model" value={currentItem?.unet_model_name || "-"} />
                      <JobRow label="Job ID" value={batchData?.job_id || "-"} />
                      <JobRow label="Item ID" value={currentItem?.item_id || "-"} />
                      <JobRow label="Results" value={batchData?.job_dir || "-"} />
                    </tbody>
                  </table>
                </Panel>
              </div>

              <Panel title="Raw Details">
                <pre
                  style={{
                    whiteSpace: "pre-wrap",
                    color: "var(--text)",
                    fontSize: "0.75rem",
                    lineHeight: 1.6,
                    margin: 0,
                  }}
                >
                  {currentAnalysis?.details || "No detailed output yet for the selected image."}
                </pre>
              </Panel>

              <div style={{ display: "flex", gap: 10, marginTop: 18, flexWrap: "wrap" }}>
                <button onClick={handleNewJob} style={secondaryLargeButtonStyle}>
                  ⟲ New Job
                </button>

                <button
                  onClick={handleExportCurrentPdf}
                  disabled={!currentAnalysis || isExporting}
                  style={runButtonStyle}
                >
                  {isExporting ? "Exporting..." : "⭳ Export Selected PDF"}
                </button>

                <button
                  onClick={handleExportBatchPdf}
                  disabled={!Object.keys(analysisMap).length || isExporting}
                  style={runButtonStyle}
                >
                  {isExporting ? "Exporting..." : "⭳ Export Batch PDF"}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </>
  );
}

function Panel({
  title,
  children,
  style,
  accentColor,
}: {
  title: string;
  children: React.ReactNode;
  style?: React.CSSProperties;
  accentColor?: string;
}) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        position: "relative",
        overflow: "hidden",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 2,
          background: accentColor
            ? accentColor
            : "linear-gradient(90deg, var(--accent), var(--accent2))",
          opacity: 0.6,
        }}
      />
      <div
        style={{
          padding: "12px 18px",
          borderBottom: "1px solid var(--border)",
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "var(--surface2)",
        }}
      >
        <div
          style={{
            width: 6,
            height: 6,
            background: accentColor || "var(--accent)",
            borderRadius: "50%",
          }}
        />
        <span
          style={{
            fontSize: "0.78rem",
            fontWeight: 700,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            color: accentColor || "var(--accent)",
          }}
        >
          {title}
        </span>
      </div>

      <div style={{ padding: 18 }}>{children}</div>
    </div>
  );
}

function Step({
  label,
  number,
  state,
}: {
  label: string;
  number: string;
  state: "done" | "active" | "idle";
}) {
  const color =
    state === "done"
      ? "var(--green)"
      : state === "active"
      ? "var(--accent)"
      : "var(--muted)";

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        fontSize: "0.72rem",
        fontWeight: 500,
        color,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
      }}
    >
      <div
        style={{
          width: 24,
          height: 24,
          borderRadius: 4,
          border: "1px solid currentColor",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "0.68rem",
          fontWeight: 700,
          flexShrink: 0,
          background:
            state === "active"
              ? "rgba(0,212,255,0.1)"
              : state === "done"
              ? "rgba(0,255,157,0.1)"
              : "transparent",
          boxShadow: state === "active" ? "0 0 8px rgba(0,212,255,0.4)" : "none",
        }}
      >
        {state === "done" ? "✓" : number}
      </div>
      {label}
    </div>
  );
}

function StepLine({ done }: { done: boolean }) {
  return (
    <div
      style={{
        flex: 1,
        height: 1,
        background: done ? "var(--green)" : "var(--border)",
        margin: "0 14px",
        minWidth: 30,
        position: "relative",
      }}
    >
      <span
        style={{
          position: "absolute",
          right: -5,
          top: -7,
          fontSize: "0.55rem",
          color: done ? "var(--green)" : "var(--border)",
        }}
      >
        ▶
      </span>
    </div>
  );
}

function ImageFrame({
  src,
  caption,
  height = 190,
}: {
  src: string;
  caption: string;
  height?: number;
}) {
  return (
    <div
      style={{
        border: "1px solid var(--border)",
        borderRadius: 4,
        overflow: "hidden",
        background: "#000",
      }}
    >
      <div
        style={{
          width: "100%",
          minHeight: height,
          background: "#000",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {src ? (
          <img
            src={src}
            alt={caption}
            style={{
              width: "100%",
              height,
              objectFit: "contain",
              display: "block",
              background: "#000",
            }}
          />
        ) : (
          <div style={{ color: "var(--muted)", fontSize: "0.72rem" }}>
            No preview available
          </div>
        )}
      </div>
      <div
        style={{
          fontSize: "0.65rem",
          padding: "4px 10px",
          background: "var(--surface2)",
          borderTop: "1px solid var(--border)",
          color: "var(--muted)",
        }}
      >
        {caption}
      </div>
    </div>
  );
}

function ResultsImage({
  label,
  src,
  caption,
}: {
  label: string;
  src: string;
  caption: string;
}) {
  return (
    <div>
      <div style={smallLabelStyle}>{label}</div>
      <ImageFrame src={src} caption={caption} height={160} />
    </div>
  );
}

function RadioOption({
  active,
  accent,
  onClick,
  label,
  icon,
}: {
  active: boolean;
  accent: "green" | "accent";
  onClick: () => void;
  label: string;
  icon: string;
}) {
  const borderColor = active
    ? accent === "green"
      ? "var(--green)"
      : "var(--accent)"
    : "var(--border)";

  const color = active
    ? accent === "green"
      ? "var(--green)"
      : "var(--accent)"
    : "var(--text)";

  const background = active
    ? accent === "green"
      ? "rgba(0,255,157,0.05)"
      : "rgba(0,212,255,0.05)"
    : "var(--surface2)";

  return (
    <div
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
        padding: "8px 12px",
        borderRadius: 4,
        border: `1px solid ${borderColor}`,
        background,
        marginBottom: 8,
        cursor: "pointer",
        fontSize: "0.8rem",
        color,
      }}
    >
      <span>{icon}</span>
      {label}
    </div>
  );
}

function JobRow({ label, value }: { label: string; value: string }) {
  return (
    <tr style={{ borderBottom: "1px solid var(--border)" }}>
      <td
        style={{
          padding: "7px 0",
          color: "var(--muted)",
          textTransform: "uppercase",
          fontSize: "0.68rem",
          letterSpacing: "0.06em",
        }}
      >
        {label}
      </td>
      <td
        style={{
          padding: "7px 0",
          color: "var(--text)",
          fontSize: "0.68rem",
          textAlign: "right",
          wordBreak: "break-word",
        }}
      >
        {value}
      </td>
    </tr>
  );
}

const smallLabelStyle: React.CSSProperties = {
  fontSize: "0.65rem",
  textTransform: "uppercase",
  letterSpacing: "0.1em",
  color: "var(--muted)",
  marginBottom: 5,
  fontWeight: 700,
};

const runButtonStyle: React.CSSProperties = {
  background: "linear-gradient(135deg, var(--accent), var(--accent2))",
  color: "#fff",
  border: "none",
  borderRadius: 5,
  padding: "11px 32px",
  fontSize: "0.95rem",
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  gap: 8,
  boxShadow: "0 0 20px rgba(0,212,255,0.25)",
};

const secondaryLargeButtonStyle: React.CSSProperties = {
  background: "var(--surface2)",
  boxShadow: "none",
  border: "1px solid var(--border)",
  color: "var(--muted)",
  borderRadius: 5,
  padding: "9px 20px",
  fontSize: "0.82rem",
  fontWeight: 700,
  cursor: "pointer",
};

const secondaryButtonStyle: React.CSSProperties = {
  background: "var(--surface2)",
  border: "1px solid var(--border)",
  color: "var(--muted)",
  padding: "6px 14px",
  borderRadius: 4,
  fontSize: "0.73rem",
  cursor: "pointer",
};

const tabButtonStyle = (active: boolean): React.CSSProperties => ({
  padding: "6px 16px",
  background: active ? "rgba(0,212,255,0.1)" : "var(--surface)",
  border: active ? "1px solid var(--accent)" : "1px solid var(--border)",
  borderRadius: 4,
  fontSize: "0.73rem",
  color: active ? "var(--accent)" : "var(--muted)",
  cursor: "pointer",
});

const toolButtonStyle = (active: boolean): React.CSSProperties => ({
  background: active ? "rgba(0,212,255,0.12)" : "var(--surface2)",
  border: active ? "1px solid var(--accent)" : "1px solid var(--border)",
  color: active ? "var(--accent)" : "var(--muted)",
  padding: "6px 14px",
  borderRadius: 4,
  fontSize: "0.73rem",
  cursor: "pointer",
  boxShadow: active ? "0 0 8px rgba(0,212,255,0.15)" : "none",
});
