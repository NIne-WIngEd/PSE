module.exports = [
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[project]/afm-frontend/app/page.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>Home
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/afm-frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$styled$2d$jsx$2f$style$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/afm-frontend/node_modules/styled-jsx/style.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/afm-frontend/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
"use client";
;
;
;
const BACKEND_URL = "http://127.0.0.1:8050";
const CANVAS_SIZE = 520;
function getOrCreateClientSessionId() {
    if ("TURBOPACK compile-time truthy", 1) return "";
    //TURBOPACK unreachable
    ;
    const key = undefined;
    const existing = undefined;
    const created = undefined;
}
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}
function Home() {
    const canvasRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])(null);
    const isDrawingRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])(false);
    const hiddenFileInputRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useRef"])(null);
    const [clientSessionId, setClientSessionId] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("");
    const [selectedFiles, setSelectedFiles] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])([]);
    const [batchData, setBatchData] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(null);
    const [selectedItemId, setSelectedItemId] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("");
    const [analysisMap, setAnalysisMap] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])({});
    const [editedMaskMap, setEditedMaskMap] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])({});
    const [status, setStatus] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("SYSTEM READY — Upload one or more AFM images to begin.");
    const [activeTab, setActiveTab] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("upload");
    const [toolMode, setToolMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("draw");
    const [brushSize, setBrushSize] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(10);
    const [maskMode, setMaskMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])("edit");
    const [strokeCount, setStrokeCount] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(0);
    const [isUploading, setIsUploading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const [isRunning, setIsRunning] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    const [isExporting, setIsExporting] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])(false);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        setClientSessionId(getOrCreateClientSessionId());
    }, []);
    const currentItem = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMemo"])(()=>{
        if (!batchData?.items?.length) return null;
        return batchData.items.find((item)=>item.item_id === selectedItemId) || batchData.items[0];
    }, [
        batchData,
        selectedItemId
    ]);
    const currentAnalysis = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMemo"])(()=>{
        if (!currentItem) return null;
        return analysisMap[currentItem.item_id] || null;
    }, [
        analysisMap,
        currentItem
    ]);
    const sortedProbabilities = (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useMemo"])(()=>{
        if (!currentItem?.probabilities) return [];
        return Object.entries(currentItem.probabilities).sort((a, b)=>b[1] - a[1]);
    }, [
        currentItem
    ]);
    const currentStep = Object.keys(analysisMap).length > 0 ? 3 : currentItem ? 2 : 1;
    const getCanvasContext = ()=>{
        const canvas = canvasRef.current;
        if (!canvas) return null;
        return canvas.getContext("2d");
    };
    const getCanvasDataUrl = ()=>{
        const canvas = canvasRef.current;
        if (!canvas) return "";
        return canvas.toDataURL("image/png");
    };
    const loadMaskToCanvas = (src)=>{
        const canvas = canvasRef.current;
        const ctx = getCanvasContext();
        if (!canvas || !ctx) return;
        const img = new Image();
        img.onload = ()=>{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        };
        img.src = src;
    };
    const saveCurrentCanvasForItem = (itemId)=>{
        if (!itemId || !canvasRef.current) return;
        if (maskMode !== "edit") return;
        const dataUrl = getCanvasDataUrl();
        if (!dataUrl) return;
        setEditedMaskMap((prev)=>({
                ...prev,
                [itemId]: dataUrl
            }));
    };
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        if (!currentItem?.item_id) return;
        const editedVersion = editedMaskMap[currentItem.item_id];
        if (editedVersion) {
            loadMaskToCanvas(editedVersion);
        } else if (currentItem.mask_image_url) {
            loadMaskToCanvas(currentItem.mask_image_url);
        }
        setStrokeCount(0);
        setMaskMode("edit");
    }, [
        currentItem?.item_id,
        editedMaskMap,
        currentItem?.mask_image_url
    ]);
    const getCanvasPoint = (e)=>{
        const canvas = canvasRef.current;
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left) * (canvas.width / rect.width),
            y: (e.clientY - rect.top) * (canvas.height / rect.height)
        };
    };
    const beginPathAt = (x, y)=>{
        const ctx = getCanvasContext();
        if (!ctx) return;
        ctx.beginPath();
        ctx.moveTo(x, y);
    };
    const drawDot = (x, y)=>{
        const ctx = getCanvasContext();
        if (!ctx) return;
        ctx.beginPath();
        ctx.fillStyle = toolMode === "draw" ? "white" : "black";
        ctx.arc(x, y, Math.max(brushSize / 2, 1), 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(x, y);
    };
    const startDrawing = (e)=>{
        if (maskMode !== "edit") return;
        isDrawingRef.current = true;
        const point = getCanvasPoint(e);
        if (!point) return;
        beginPathAt(point.x, point.y);
        drawDot(point.x, point.y);
        setStrokeCount((prev)=>prev + 1);
    };
    const stopDrawing = ()=>{
        isDrawingRef.current = false;
        const ctx = getCanvasContext();
        ctx?.beginPath();
        if (currentItem?.item_id && maskMode === "edit") {
            const dataUrl = getCanvasDataUrl();
            if (dataUrl) {
                setEditedMaskMap((prev)=>({
                        ...prev,
                        [currentItem.item_id]: dataUrl
                    }));
            }
        }
    };
    const draw = (e)=>{
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
    const resetMask = ()=>{
        if (currentItem?.mask_image_url) {
            loadMaskToCanvas(currentItem.mask_image_url);
            setEditedMaskMap((prev)=>{
                const next = {
                    ...prev
                };
                delete next[currentItem.item_id];
                return next;
            });
            setStrokeCount(0);
            setStatus("MASK RESET — Restored original U-Net mask preview.");
        }
    };
    const handleNewJob = ()=>{
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
    const handleUpload = async ()=>{
        if (!selectedFiles.length) {
            setStatus("ERROR — Please choose one or more files first.");
            return;
        }
        setAnalysisMap({});
        setEditedMaskMap({});
        setIsUploading(true);
        setStatus("PROCESSING — Uploading batch and running CNN + U-Net on each image...");
        const formData = new FormData();
        selectedFiles.forEach((file)=>formData.append("files", file));
        formData.append("client_session_id", clientSessionId);
        try {
            const res = await fetch(`${BACKEND_URL}/api/upload`, {
                method: "POST",
                body: formData
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
            setStatus(`UPLOAD COMPLETE — Job ${data.job_id} created with ${data.batch_count} image${data.batch_count === 1 ? "" : "s"}.`);
            setActiveTab("upload");
        } catch (error) {
            setStatus("ERROR — Failed to connect to backend.");
            console.error(error);
        } finally{
            setIsUploading(false);
        }
    };
    const handleRunAnalysis = async ()=>{
        if (!batchData?.items?.length) {
            setStatus("ERROR — Upload a batch first.");
            return;
        }
        let editedMasksSnapshot = {
            ...editedMaskMap
        };
        if (currentItem?.item_id && maskMode === "edit" && canvasRef.current) {
            const dataUrl = getCanvasDataUrl();
            if (dataUrl) {
                editedMasksSnapshot[currentItem.item_id] = dataUrl;
                setEditedMaskMap(editedMasksSnapshot);
            }
        }
        setIsRunning(true);
        setStatus(`ANALYSIS RUNNING — Executing analysis for all ${batchData.items.length} images in this batch...`);
        try {
            const payload = {
                job_id: batchData.job_id,
                job_dir: batchData.job_dir,
                items: batchData.items,
                edited_masks_by_item_id: editedMasksSnapshot
            };
            const res = await fetch(`${BACKEND_URL}/api/run-analysis-batch`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!res.ok) {
                setStatus(`ERROR — ${data.error || "Batch analysis failed"}`);
                return;
            }
            const nextMap = {};
            for (const result of data.results || []){
                nextMap[result.item_id] = result;
            }
            setAnalysisMap(nextMap);
            setActiveTab("results");
            setStatus(`COMPLETE — Batch analysis finished for ${data.result_count || 0} image${data.result_count === 1 ? "" : "s"}.`);
        } catch (error) {
            setStatus("ERROR — Failed to connect to backend.");
            console.error(error);
        } finally{
            setIsRunning(false);
        }
    };
    const handleExportCurrentPdf = async ()=>{
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
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    batch_data: batchData,
                    current_item: currentItem,
                    current_analysis: currentAnalysis
                })
            });
            if (!res.ok) {
                const data = await res.json().catch(()=>({}));
                setStatus(`ERROR — ${data.error || "PDF export failed"}`);
                return;
            }
            const blob = await res.blob();
            const filename = `${(currentAnalysis.original_filename || "afm_result").replace(/\.[^.]+$/, "")}_analysis.pdf`;
            downloadBlob(blob, filename);
            setStatus("EXPORT COMPLETE — Selected result PDF downloaded.");
        } catch (error) {
            console.error(error);
            setStatus("ERROR — Failed to export selected PDF.");
        } finally{
            setIsExporting(false);
        }
    };
    const handleExportBatchPdf = async ()=>{
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
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    batch_data: batchData,
                    items: batchData.items,
                    analysis_results: analysisResults
                })
            });
            if (!res.ok) {
                const data = await res.json().catch(()=>({}));
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
        } finally{
            setIsExporting(false);
        }
    };
    const badgeClass = (name)=>String(name || "unknown").toUpperCase();
    const renderProbabilityBars = ()=>{
        if (!sortedProbabilities.length) {
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    color: "var(--muted)",
                    fontSize: "0.72rem"
                },
                children: "Waiting for classification results."
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 505,
                columnNumber: 9
            }, this);
        }
        const topLabel = sortedProbabilities[0][0];
        return sortedProbabilities.map(([label, value])=>{
            const pct = Math.max(0, Math.min(100, value * 100));
            const isTop = label === topLabel;
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "prob-row",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "prob-lbl",
                        children: label
                    }, void 0, false, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 519,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "prob-track",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: `prob-fill ${isTop ? "top" : ""}`,
                            style: {
                                width: `${pct}%`
                            }
                        }, void 0, false, {
                            fileName: "[project]/afm-frontend/app/page.tsx",
                            lineNumber: 521,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 520,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "prob-val",
                        children: [
                            pct.toFixed(1),
                            "%"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 526,
                        columnNumber: 11
                    }, this)
                ]
            }, label, true, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 518,
                columnNumber: 9
            }, this);
        });
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$styled$2d$jsx$2f$style$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["default"], {
                id: "494bcee0ea3a1b2a",
                children: ':root{--bg:#0a0e17;--surface:#111827;--surface2:#1a2236;--border:#1e2d45;--accent:#00d4ff;--accent2:#7c3aed;--green:#00ff9d;--yellow:#ffd60a;--text:#e2e8f0;--muted:#4a6280}*{box-sizing:border-box}html,body{background:var(--bg);color:var(--text);margin:0;padding:0;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,Courier New,monospace}body:before{content:"";z-index:9999;pointer-events:none;background:repeating-linear-gradient(0deg,#0000,#0000 2px,#0000000a 2px 4px);position:fixed;inset:0}button,input,select{font:inherit}.prob-row{grid-template-columns:72px 1fr 62px;align-items:center;gap:8px;margin-bottom:8px;display:grid}.prob-lbl{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:.7rem}.prob-track{background:var(--surface2);border:1px solid var(--border);border-radius:999px;height:10px;overflow:hidden}.prob-fill{background:#00d4ff73;height:100%}.prob-fill.top{background:linear-gradient(90deg,var(--accent),var(--accent2))}.prob-val{color:var(--accent);text-align:right;font-size:.72rem;font-weight:700}'
            }, void 0, false, void 0, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
                style: {
                    minHeight: "100vh",
                    background: "var(--bg)",
                    color: "var(--text)"
                },
                className: "jsx-494bcee0ea3a1b2a",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("nav", {
                        style: {
                            background: "var(--surface)",
                            borderBottom: "1px solid var(--border)",
                            padding: "0 32px",
                            height: 52,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            position: "sticky",
                            top: 0,
                            zIndex: 100
                        },
                        className: "jsx-494bcee0ea3a1b2a",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 10
                                },
                                className: "jsx-494bcee0ea3a1b2a",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            width: 8,
                                            height: 8,
                                            borderRadius: "50%",
                                            background: "var(--accent)",
                                            boxShadow: "0 0 12px rgba(0,212,255,0.7)"
                                        },
                                        className: "jsx-494bcee0ea3a1b2a"
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 637,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            fontWeight: 800,
                                            letterSpacing: "0.05em",
                                            fontSize: "1.1rem"
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: "AFM Analysis"
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 646,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        style: {
                                            fontSize: "0.62rem",
                                            color: "var(--muted)",
                                            letterSpacing: "0.12em",
                                            textTransform: "uppercase",
                                            alignSelf: "flex-end",
                                            marginBottom: 2
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: "// nanoscale imaging"
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 649,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 636,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 16
                                },
                                className: "jsx-494bcee0ea3a1b2a",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        style: {
                                            fontSize: "0.68rem",
                                            color: "var(--muted)",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 6
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                style: {
                                                    width: 6,
                                                    height: 6,
                                                    borderRadius: "50%",
                                                    background: "var(--green)",
                                                    boxShadow: "0 0 10px rgba(0,255,157,0.8)",
                                                    display: "inline-block"
                                                },
                                                className: "jsx-494bcee0ea3a1b2a"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 673,
                                                columnNumber: 15
                                            }, this),
                                            "SYSTEM ONLINE"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 664,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: handleNewJob,
                                        style: {
                                            background: "transparent",
                                            border: "1px solid var(--border)",
                                            color: "var(--muted)",
                                            padding: "5px 12px",
                                            borderRadius: 4,
                                            fontSize: "0.73rem",
                                            cursor: "pointer"
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: "⟳ New Job"
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 686,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 663,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 622,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        style: {
                            background: "var(--surface)",
                            borderBottom: "1px solid var(--border)",
                            padding: "10px 32px",
                            display: "flex",
                            alignItems: "center"
                        },
                        className: "jsx-494bcee0ea3a1b2a",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Step, {
                                label: "Upload & Detect",
                                number: "01",
                                state: currentStep > 1 ? "done" : currentStep === 1 ? "active" : "idle"
                            }, void 0, false, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 712,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(StepLine, {
                                done: currentStep > 1
                            }, void 0, false, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 717,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Step, {
                                label: "Review Mask",
                                number: "02",
                                state: currentStep > 2 ? "done" : currentStep === 2 ? "active" : "idle"
                            }, void 0, false, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 718,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(StepLine, {
                                done: currentStep > 2
                            }, void 0, false, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 723,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Step, {
                                label: "Analysis",
                                number: "03",
                                state: currentStep === 3 ? "active" : "idle"
                            }, void 0, false, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 724,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 703,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        style: {
                            maxWidth: 1280,
                            margin: "0 auto",
                            padding: "24px 28px"
                        },
                        className: "jsx-494bcee0ea3a1b2a",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    display: "flex",
                                    gap: 6,
                                    marginBottom: 22
                                },
                                className: "jsx-494bcee0ea3a1b2a",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>setActiveTab("upload"),
                                        style: tabButtonStyle(activeTab === "upload"),
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: "▶ Stage: Upload & Edit"
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 733,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>setActiveTab("results"),
                                        style: tabButtonStyle(activeTab === "results"),
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: "▶ Stage: Results"
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 739,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 732,
                                columnNumber: 11
                            }, this),
                            activeTab === "upload" && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                style: {
                                    display: "grid",
                                    gridTemplateColumns: "1fr 1.35fr",
                                    gap: 18
                                },
                                className: "jsx-494bcee0ea3a1b2a",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            display: "flex",
                                            flexDirection: "column",
                                            gap: 16
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "Input Batch",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        onClick: ()=>hiddenFileInputRef.current?.click(),
                                                        style: {
                                                            border: "1px dashed var(--border)",
                                                            borderRadius: 6,
                                                            padding: "36px 24px",
                                                            textAlign: "center",
                                                            cursor: "pointer",
                                                            background: "rgba(0,212,255,0.02)"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                ref: hiddenFileInputRef,
                                                                type: "file",
                                                                accept: ".jpg,.jpeg,.png,.tif,.tiff",
                                                                multiple: true,
                                                                onChange: (e)=>{
                                                                    const files = Array.from(e.target.files || []);
                                                                    setSelectedFiles(files);
                                                                },
                                                                style: {
                                                                    display: "none"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 762,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    fontSize: "2.4rem",
                                                                    color: "var(--accent)",
                                                                    opacity: 0.8
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "⤴"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 773,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    fontSize: "1rem",
                                                                    fontWeight: 700,
                                                                    letterSpacing: "0.05em"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: selectedFiles.length ? `${selectedFiles.length} file${selectedFiles.length === 1 ? "" : "s"} selected` : "Drop AFM Images Here"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 776,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    fontSize: "0.73rem",
                                                                    color: "var(--muted)",
                                                                    marginTop: 4
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: selectedFiles.length ? "Batch ready — click upload below" : "or click to browse multiple files"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 781,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 751,
                                                        columnNumber: 19
                                                    }, this),
                                                    !!selectedFiles.length && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            marginTop: 12
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: smallLabelStyle,
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Selected Files"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 790,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    maxHeight: 180,
                                                                    overflowY: "auto",
                                                                    border: "1px solid var(--border)",
                                                                    borderRadius: 6,
                                                                    background: "var(--surface2)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: selectedFiles.map((file, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                        style: {
                                                                            padding: "8px 10px",
                                                                            borderBottom: idx === selectedFiles.length - 1 ? "none" : "1px solid var(--border)",
                                                                            fontSize: "0.74rem",
                                                                            color: "var(--text)"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a",
                                                                        children: [
                                                                            idx + 1,
                                                                            ". ",
                                                                            file.name
                                                                        ]
                                                                    }, `${file.name}-${idx}`, true, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 801,
                                                                        columnNumber: 27
                                                                    }, this))
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 791,
                                                                columnNumber: 23
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 789,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            marginTop: 14,
                                                            display: "flex",
                                                            gap: 10,
                                                            alignItems: "center",
                                                            flexWrap: "wrap"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                                onClick: handleUpload,
                                                                disabled: isUploading,
                                                                style: runButtonStyle,
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: isUploading ? "Running..." : "Upload Batch"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 819,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
                                                                    fontSize: "0.73rem",
                                                                    color: "var(--muted)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "// one job id for the whole batch"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 822,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 818,
                                                        columnNumber: 19
                                                    }, this),
                                                    batchData && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            marginTop: 12,
                                                            fontSize: "0.72rem",
                                                            color: "var(--muted)"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            "Job ID: ",
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
                                                                    color: "var(--accent)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: batchData.job_id
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 829,
                                                                columnNumber: 31
                                                            }, this),
                                                            " · ",
                                                            "Batch Count: ",
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
                                                                    color: "var(--accent)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: batchData.batch_count
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 831,
                                                                columnNumber: 36
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 828,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 750,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "Batch Items",
                                                children: batchData?.items?.length ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    style: {
                                                        display: "flex",
                                                        flexDirection: "column",
                                                        gap: 8
                                                    },
                                                    className: "jsx-494bcee0ea3a1b2a",
                                                    children: batchData.items.map((item)=>{
                                                        const isSelected = item.item_id === currentItem?.item_id;
                                                        const isDone = !!analysisMap[item.item_id];
                                                        const isEdited = !!editedMaskMap[item.item_id];
                                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                            onClick: ()=>{
                                                                saveCurrentCanvasForItem(currentItem?.item_id);
                                                                setSelectedItemId(item.item_id);
                                                                setActiveTab("upload");
                                                            },
                                                            style: {
                                                                textAlign: "left",
                                                                padding: "10px 12px",
                                                                borderRadius: 6,
                                                                border: isSelected ? "1px solid var(--accent)" : "1px solid var(--border)",
                                                                background: isSelected ? "rgba(0,212,255,0.08)" : "var(--surface2)",
                                                                color: "var(--text)",
                                                                cursor: "pointer"
                                                            },
                                                            className: "jsx-494bcee0ea3a1b2a",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    style: {
                                                                        fontSize: "0.76rem",
                                                                        fontWeight: 700
                                                                    },
                                                                    className: "jsx-494bcee0ea3a1b2a",
                                                                    children: [
                                                                        item.item_index,
                                                                        ". ",
                                                                        item.original_filename
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                                    lineNumber: 866,
                                                                    columnNumber: 29
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    style: {
                                                                        fontSize: "0.68rem",
                                                                        color: "var(--muted)",
                                                                        marginTop: 4
                                                                    },
                                                                    className: "jsx-494bcee0ea3a1b2a",
                                                                    children: [
                                                                        "Class: ",
                                                                        badgeClass(item.predicted_class),
                                                                        " · Confidence:",
                                                                        " ",
                                                                        (item.confidence * 100).toFixed(1),
                                                                        "% ·",
                                                                        " ",
                                                                        isDone ? "Analysis complete" : isEdited ? "Edited mask saved" : "Pending analysis"
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                                    lineNumber: 869,
                                                                    columnNumber: 29
                                                                }, this)
                                                            ]
                                                        }, item.item_id, true, {
                                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                                            lineNumber: 845,
                                                            columnNumber: 27
                                                        }, this);
                                                    })
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 838,
                                                    columnNumber: 21
                                                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    style: {
                                                        color: "var(--muted)",
                                                        fontSize: "0.74rem"
                                                    },
                                                    className: "jsx-494bcee0ea3a1b2a",
                                                    children: "No batch uploaded yet."
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 879,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 836,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "CNN Classification",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            display: "flex",
                                                            alignItems: "center",
                                                            marginBottom: 14,
                                                            flexWrap: "wrap",
                                                            gap: 10
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
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
                                                                    border: "1px solid rgba(0,212,255,0.3)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: [
                                                                    "CPU ",
                                                                    currentItem ? badgeClass(currentItem.predicted_class) : "WAITING"
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 887,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
                                                                    fontSize: "0.75rem",
                                                                    color: "var(--muted)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: currentItem ? `${(currentItem.confidence * 100).toFixed(1)}% confidence` : "No prediction yet"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 905,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 886,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: renderProbabilityBars()
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 912,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            marginTop: 16
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: smallLabelStyle,
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Original Image"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 915,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ImageFrame, {
                                                                src: currentItem?.original_image_url || "",
                                                                caption: currentItem?.saved_filename || "No image loaded",
                                                                height: 240
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 916,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 914,
                                                        columnNumber: 19
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 885,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 749,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "U-Net Segmentation Mask",
                                                style: {
                                                    marginBottom: 16
                                                },
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                        style: {
                                                            fontSize: "0.76rem",
                                                            color: "var(--muted)",
                                                            lineHeight: 1.65,
                                                            marginBottom: 14
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            "Automatic segmentation complete.",
                                                            " ",
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
                                                                    color: "var(--text)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "White regions"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 936,
                                                                columnNumber: 21
                                                            }, this),
                                                            " = detected features.",
                                                            " ",
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                style: {
                                                                    color: "var(--text)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Black"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 937,
                                                                columnNumber: 21
                                                            }, this),
                                                            " = background. Verify the mask for the selected batch item."
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 927,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ImageFrame, {
                                                        src: currentItem?.mask_image_url || "",
                                                        caption: currentItem?.mask_filename || "unet_mask_preview.png",
                                                        height: 260
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 941,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            marginTop: 14
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                style: {
                                                                    fontSize: "0.76rem",
                                                                    fontWeight: 600,
                                                                    color: "var(--text)",
                                                                    marginBottom: 8,
                                                                    textTransform: "uppercase",
                                                                    letterSpacing: "0.06em"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Proceed with selected mask?"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 948,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(RadioOption, {
                                                                active: maskMode === "use",
                                                                accent: "green",
                                                                onClick: ()=>setMaskMode("use"),
                                                                label: "Use mask as-is",
                                                                icon: "▶"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 961,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(RadioOption, {
                                                                active: maskMode === "edit",
                                                                accent: "accent",
                                                                onClick: ()=>setMaskMode("edit"),
                                                                label: "Open editor to correct the mask",
                                                                icon: "✎"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 968,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 947,
                                                        columnNumber: 19
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 926,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "Mask Editor",
                                                accentColor: "var(--accent2)",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            display: "flex",
                                                            gap: 16,
                                                            marginBottom: 12,
                                                            flexWrap: "wrap"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    display: "flex",
                                                                    alignItems: "center",
                                                                    gap: 6,
                                                                    fontSize: "0.72rem",
                                                                    color: "var(--muted)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                        style: {
                                                                            width: 14,
                                                                            height: 14,
                                                                            borderRadius: 2,
                                                                            border: "1px solid #555",
                                                                            background: "#fff"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 981,
                                                                        columnNumber: 23
                                                                    }, this),
                                                                    "White = draw features"
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 980,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    display: "flex",
                                                                    alignItems: "center",
                                                                    gap: 6,
                                                                    fontSize: "0.72rem",
                                                                    color: "var(--muted)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                        style: {
                                                                            width: 14,
                                                                            height: 14,
                                                                            borderRadius: 2,
                                                                            border: "1px solid var(--accent)",
                                                                            background: "#111"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 985,
                                                                        columnNumber: 23
                                                                    }, this),
                                                                    "Black = erase features"
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 984,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 979,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            display: "flex",
                                                            gap: 8,
                                                            marginBottom: 12,
                                                            alignItems: "center",
                                                            flexWrap: "wrap"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                                onClick: ()=>setToolMode("draw"),
                                                                style: toolButtonStyle(toolMode === "draw"),
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Brush Draw (white)"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 991,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                                onClick: ()=>setToolMode("erase"),
                                                                style: toolButtonStyle(toolMode === "erase"),
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Erase (black)"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 995,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                                onClick: resetMask,
                                                                style: secondaryButtonStyle,
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: "Reset Mask"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 999,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    flex: 1,
                                                                    display: "flex",
                                                                    alignItems: "center",
                                                                    gap: 8,
                                                                    marginLeft: 10,
                                                                    minWidth: 220
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                        style: {
                                                                            fontSize: "0.68rem",
                                                                            color: "var(--muted)",
                                                                            whiteSpace: "nowrap"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a",
                                                                        children: "Brush px:"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 1013,
                                                                        columnNumber: 23
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                        type: "range",
                                                                        min: 2,
                                                                        max: 40,
                                                                        value: brushSize,
                                                                        onChange: (e)=>setBrushSize(Number(e.target.value)),
                                                                        style: {
                                                                            flex: 1,
                                                                            accentColor: "#00d4ff"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 1016,
                                                                        columnNumber: 23
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                        style: {
                                                                            fontSize: "0.68rem",
                                                                            color: "var(--accent)",
                                                                            minWidth: 24
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a",
                                                                        children: brushSize
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 1024,
                                                                        columnNumber: 23
                                                                    }, this)
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1003,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 990,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        style: {
                                                            width: "100%",
                                                            minHeight: 300,
                                                            background: "#050810",
                                                            border: "1px solid var(--border)",
                                                            borderRadius: 4,
                                                            display: "flex",
                                                            alignItems: "center",
                                                            justifyContent: "center",
                                                            position: "relative",
                                                            overflow: "hidden"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    position: "absolute",
                                                                    inset: 0,
                                                                    backgroundImage: "linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px)",
                                                                    backgroundSize: "24px 24px"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1044,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    position: "absolute",
                                                                    width: 1,
                                                                    height: "100%",
                                                                    background: "rgba(0,212,255,0.1)",
                                                                    left: "50%"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1053,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    position: "absolute",
                                                                    width: "100%",
                                                                    height: 1,
                                                                    background: "rgba(0,212,255,0.1)",
                                                                    top: "50%"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1062,
                                                                columnNumber: 21
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                style: {
                                                                    position: "relative",
                                                                    zIndex: 1,
                                                                    padding: 12
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    style: {
                                                                        border: "1px solid var(--border)",
                                                                        borderRadius: 4,
                                                                        overflow: "hidden",
                                                                        background: "#000",
                                                                        boxShadow: "0 0 20px rgba(0,212,255,0.08)"
                                                                    },
                                                                    className: "jsx-494bcee0ea3a1b2a",
                                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("canvas", {
                                                                        ref: canvasRef,
                                                                        width: CANVAS_SIZE,
                                                                        height: CANVAS_SIZE,
                                                                        onMouseDown: startDrawing,
                                                                        onMouseUp: stopDrawing,
                                                                        onMouseLeave: stopDrawing,
                                                                        onMouseMove: draw,
                                                                        style: {
                                                                            display: "block",
                                                                            width: "100%",
                                                                            maxWidth: 520,
                                                                            height: "auto",
                                                                            cursor: maskMode === "edit" ? "crosshair" : "not-allowed",
                                                                            pointerEvents: currentItem && maskMode === "edit" ? "auto" : "none",
                                                                            background: "#000"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 1082,
                                                                        columnNumber: 25
                                                                    }, this)
                                                                }, void 0, false, {
                                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                                    lineNumber: 1073,
                                                                    columnNumber: 23
                                                                }, this)
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1072,
                                                                columnNumber: 21
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1030,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                        style: {
                                                            fontSize: "0.68rem",
                                                            color: "var(--muted)",
                                                            marginTop: 8
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            "↳ ",
                                                            strokeCount,
                                                            " stroke",
                                                            strokeCount === 1 ? "" : "s",
                                                            " recorded for current image.",
                                                            currentItem?.item_id && editedMaskMap[currentItem.item_id] ? " Edited mask saved for batch run." : ""
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1104,
                                                        columnNumber: 19
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 978,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                style: {
                                                    display: "flex",
                                                    alignItems: "center",
                                                    padding: "16px 0",
                                                    flexWrap: "wrap",
                                                    gap: 10
                                                },
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                        onClick: handleRunAnalysis,
                                                        disabled: isRunning || !batchData?.items?.length,
                                                        style: runButtonStyle,
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: isRunning ? "Running..." : "Execute Full Batch"
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1113,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        style: {
                                                            fontSize: "0.73rem",
                                                            color: "var(--muted)"
                                                        },
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: "// one click analyzes every image in this batch"
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1120,
                                                        columnNumber: 19
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1112,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                style: {
                                                    display: "flex",
                                                    alignItems: "center",
                                                    gap: 10,
                                                    padding: "10px 14px",
                                                    borderRadius: 4,
                                                    fontSize: "0.78rem",
                                                    border: "1px solid rgba(0,212,255,0.25)",
                                                    background: "rgba(0,212,255,0.06)",
                                                    color: "var(--accent)",
                                                    whiteSpace: "pre-wrap"
                                                },
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: "●"
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1139,
                                                        columnNumber: 19
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: status
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1140,
                                                        columnNumber: 19
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1125,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 925,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 748,
                                columnNumber: 13
                            }, this),
                            activeTab === "results" && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "jsx-494bcee0ea3a1b2a",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                        title: "Batch Results Navigator",
                                        style: {
                                            marginBottom: 18
                                        },
                                        children: batchData?.items?.length ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            style: {
                                                display: "grid",
                                                gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
                                                gap: 10
                                            },
                                            className: "jsx-494bcee0ea3a1b2a",
                                            children: batchData.items.map((item)=>{
                                                const isSelected = item.item_id === currentItem?.item_id;
                                                const isDone = !!analysisMap[item.item_id];
                                                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                    onClick: ()=>setSelectedItemId(item.item_id),
                                                    style: {
                                                        textAlign: "left",
                                                        padding: "10px 12px",
                                                        borderRadius: 6,
                                                        border: isSelected ? "1px solid var(--accent)" : "1px solid var(--border)",
                                                        background: isSelected ? "rgba(0,212,255,0.08)" : "var(--surface2)",
                                                        color: "var(--text)",
                                                        cursor: "pointer"
                                                    },
                                                    className: "jsx-494bcee0ea3a1b2a",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            style: {
                                                                fontSize: "0.76rem",
                                                                fontWeight: 700
                                                            },
                                                            className: "jsx-494bcee0ea3a1b2a",
                                                            children: item.original_filename
                                                        }, void 0, false, {
                                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                                            lineNumber: 1172,
                                                            columnNumber: 27
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            style: {
                                                                fontSize: "0.68rem",
                                                                color: "var(--muted)",
                                                                marginTop: 4
                                                            },
                                                            className: "jsx-494bcee0ea3a1b2a",
                                                            children: [
                                                                badgeClass(item.predicted_class),
                                                                " ·",
                                                                " ",
                                                                isDone ? "Analyzed" : "Not analyzed yet"
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                                            lineNumber: 1175,
                                                            columnNumber: 27
                                                        }, this)
                                                    ]
                                                }, item.item_id, true, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1155,
                                                    columnNumber: 25
                                                }, this);
                                            })
                                        }, void 0, false, {
                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                            lineNumber: 1150,
                                            columnNumber: 19
                                        }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            style: {
                                                color: "var(--muted)",
                                                fontSize: "0.74rem"
                                            },
                                            className: "jsx-494bcee0ea3a1b2a",
                                            children: "No batch available."
                                        }, void 0, false, {
                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                            lineNumber: 1184,
                                            columnNumber: 19
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1148,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 10,
                                            padding: "10px 14px",
                                            borderRadius: 4,
                                            fontSize: "0.78rem",
                                            border: "1px solid rgba(0,255,157,0.25)",
                                            background: "rgba(0,255,157,0.06)",
                                            color: "var(--green)",
                                            marginBottom: 18
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: "✔"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1204,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: currentAnalysis ? `ANALYSIS COMPLETE — ${currentAnalysis.summary}` : "No analysis result yet for the selected image."
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1205,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1190,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 14,
                                            flexWrap: "wrap",
                                            background: "var(--surface)",
                                            border: "1px solid rgba(0,212,255,0.2)",
                                            borderRadius: 6,
                                            padding: "12px 18px",
                                            marginBottom: 18
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                style: {
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
                                                    border: "1px solid rgba(0,212,255,0.3)"
                                                },
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: currentItem ? badgeClass(currentItem.predicted_class) : "WAITING"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1225,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                style: {
                                                    fontSize: "0.76rem",
                                                    color: "var(--muted)"
                                                },
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: currentItem ? `${(currentItem.confidence * 100).toFixed(1)}% confidence · ${currentItem.cnn_model_name} · ${currentItem.unet_model_name}` : "Select an image"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1243,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1212,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                        title: "Image Outputs",
                                        style: {
                                            marginBottom: 18
                                        },
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            style: {
                                                display: "grid",
                                                gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
                                                gap: 14
                                            },
                                            className: "jsx-494bcee0ea3a1b2a",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                    label: "Original",
                                                    src: currentAnalysis?.original_image_url || currentItem?.original_image_url || "",
                                                    caption: currentAnalysis?.original_filename || currentItem?.saved_filename || "sample"
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1258,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                    label: "Final Mask",
                                                    src: currentAnalysis?.final_mask_url || "",
                                                    caption: currentAnalysis?.final_mask_filename || "unet_mask_final.png"
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1263,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                    label: currentAnalysis?.extra1_note || "Extra Output 1",
                                                    src: currentAnalysis?.extra1_url || "",
                                                    caption: currentAnalysis?.extra1_note || "extra_output_1.png"
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1268,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                    label: currentAnalysis?.extra2_note || "Extra Output 2",
                                                    src: currentAnalysis?.extra2_url || "",
                                                    caption: currentAnalysis?.extra2_note || "extra_output_2.png"
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1273,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                    label: currentAnalysis?.extra3_note || "Extra Output 3",
                                                    src: currentAnalysis?.extra3_url || "",
                                                    caption: currentAnalysis?.extra3_note || "extra_output_3.png"
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1278,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                    label: currentAnalysis?.extra4_note || "Extra Output 4",
                                                    src: currentAnalysis?.extra4_url || "",
                                                    caption: currentAnalysis?.extra4_note || "extra_output_4.png"
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1283,
                                                    columnNumber: 19
                                                }, this),
                                                currentAnalysis?.additional_outputs?.map((img, idx)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ResultsImage, {
                                                        label: img.label,
                                                        src: img.url,
                                                        caption: img.label
                                                    }, `${img.label}-${idx}`, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1290,
                                                        columnNumber: 21
                                                    }, this))
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                            lineNumber: 1251,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1250,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            display: "grid",
                                            gridTemplateColumns: "1fr 1fr",
                                            gap: 16,
                                            marginBottom: 18
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "Analysis Metrics",
                                                children: currentAnalysis?.metrics?.length ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                                                    style: {
                                                        width: "100%",
                                                        borderCollapse: "collapse",
                                                        fontSize: "0.76rem"
                                                    },
                                                    className: "jsx-494bcee0ea3a1b2a",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: currentAnalysis.metrics.map((metric)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                                                style: {
                                                                    borderBottom: "1px solid var(--border)"
                                                                },
                                                                className: "jsx-494bcee0ea3a1b2a",
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                                        style: {
                                                                            padding: "7px 0",
                                                                            color: "var(--muted)",
                                                                            textTransform: "uppercase",
                                                                            fontSize: "0.68rem",
                                                                            letterSpacing: "0.06em"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a",
                                                                        children: metric.label
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 1314,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                                        style: {
                                                                            padding: "7px 0",
                                                                            color: "var(--accent)",
                                                                            fontWeight: 700,
                                                                            textAlign: "right"
                                                                        },
                                                                        className: "jsx-494bcee0ea3a1b2a",
                                                                        children: metric.value
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                                        lineNumber: 1325,
                                                                        columnNumber: 29
                                                                    }, this)
                                                                ]
                                                            }, metric.key, true, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1313,
                                                                columnNumber: 27
                                                            }, this))
                                                    }, void 0, false, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1311,
                                                        columnNumber: 23
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1310,
                                                    columnNumber: 21
                                                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    style: {
                                                        color: "var(--muted)",
                                                        fontSize: "0.76rem"
                                                    },
                                                    className: "jsx-494bcee0ea3a1b2a",
                                                    children: "No analysis has been run yet for the selected image."
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1340,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1308,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                                title: "Job Details",
                                                accentColor: "var(--muted)",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                                                    style: {
                                                        width: "100%",
                                                        borderCollapse: "collapse",
                                                        fontSize: "0.76rem"
                                                    },
                                                    className: "jsx-494bcee0ea3a1b2a",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                                                        className: "jsx-494bcee0ea3a1b2a",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(JobRow, {
                                                                label: "CNN model",
                                                                value: currentItem?.cnn_model_name || "-"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1349,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(JobRow, {
                                                                label: "U-Net model",
                                                                value: currentItem?.unet_model_name || "-"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1350,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(JobRow, {
                                                                label: "Job ID",
                                                                value: batchData?.job_id || "-"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1351,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(JobRow, {
                                                                label: "Item ID",
                                                                value: currentItem?.item_id || "-"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1352,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(JobRow, {
                                                                label: "Results",
                                                                value: batchData?.job_dir || "-"
                                                            }, void 0, false, {
                                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                                lineNumber: 1353,
                                                                columnNumber: 23
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                                        lineNumber: 1348,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/afm-frontend/app/page.tsx",
                                                    lineNumber: 1347,
                                                    columnNumber: 19
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1346,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1300,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(Panel, {
                                        title: "Raw Details",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("pre", {
                                            style: {
                                                whiteSpace: "pre-wrap",
                                                color: "var(--text)",
                                                fontSize: "0.75rem",
                                                lineHeight: 1.6,
                                                margin: 0
                                            },
                                            className: "jsx-494bcee0ea3a1b2a",
                                            children: currentAnalysis?.details || "No detailed output yet for the selected image."
                                        }, void 0, false, {
                                            fileName: "[project]/afm-frontend/app/page.tsx",
                                            lineNumber: 1360,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1359,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        style: {
                                            display: "flex",
                                            gap: 10,
                                            marginTop: 18,
                                            flexWrap: "wrap"
                                        },
                                        className: "jsx-494bcee0ea3a1b2a",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                onClick: handleNewJob,
                                                style: secondaryLargeButtonStyle,
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: "⟲ New Job"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1374,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                onClick: handleExportCurrentPdf,
                                                disabled: !currentAnalysis || isExporting,
                                                style: runButtonStyle,
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: isExporting ? "Exporting..." : "⭳ Export Selected PDF"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1378,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                onClick: handleExportBatchPdf,
                                                disabled: !Object.keys(analysisMap).length || isExporting,
                                                style: runButtonStyle,
                                                className: "jsx-494bcee0ea3a1b2a",
                                                children: isExporting ? "Exporting..." : "⭳ Export Batch PDF"
                                            }, void 0, false, {
                                                fileName: "[project]/afm-frontend/app/page.tsx",
                                                lineNumber: 1386,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/afm-frontend/app/page.tsx",
                                        lineNumber: 1373,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/afm-frontend/app/page.tsx",
                                lineNumber: 1147,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 731,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 621,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true);
}
function Panel({ title, children, style, accentColor }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        style: {
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 6,
            position: "relative",
            overflow: "hidden",
            ...style
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 2,
                    background: accentColor ? accentColor : "linear-gradient(90deg, var(--accent), var(--accent2))",
                    opacity: 0.6
                }
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1424,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    padding: "12px 18px",
                    borderBottom: "1px solid var(--border)",
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    background: "var(--surface2)"
                },
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        style: {
                            width: 6,
                            height: 6,
                            background: accentColor || "var(--accent)",
                            borderRadius: "50%"
                        }
                    }, void 0, false, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 1447,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        style: {
                            fontSize: "0.78rem",
                            fontWeight: 700,
                            letterSpacing: "0.14em",
                            textTransform: "uppercase",
                            color: accentColor || "var(--accent)"
                        },
                        children: title
                    }, void 0, false, {
                        fileName: "[project]/afm-frontend/app/page.tsx",
                        lineNumber: 1455,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1437,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    padding: 18
                },
                children: children
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1468,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1414,
        columnNumber: 5
    }, this);
}
function Step({ label, number, state }) {
    const color = state === "done" ? "var(--green)" : state === "active" ? "var(--accent)" : "var(--muted)";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        style: {
            display: "flex",
            alignItems: "center",
            gap: 8,
            fontSize: "0.72rem",
            fontWeight: 500,
            color,
            letterSpacing: "0.06em",
            textTransform: "uppercase"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
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
                    background: state === "active" ? "rgba(0,212,255,0.1)" : state === "done" ? "rgba(0,255,157,0.1)" : "transparent",
                    boxShadow: state === "active" ? "0 0 8px rgba(0,212,255,0.4)" : "none"
                },
                children: state === "done" ? "✓" : number
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1502,
                columnNumber: 7
            }, this),
            label
        ]
    }, void 0, true, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1490,
        columnNumber: 5
    }, this);
}
function StepLine({ done }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        style: {
            flex: 1,
            height: 1,
            background: done ? "var(--green)" : "var(--border)",
            margin: "0 14px",
            minWidth: 30,
            position: "relative"
        },
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
            style: {
                position: "absolute",
                right: -5,
                top: -7,
                fontSize: "0.55rem",
                color: done ? "var(--green)" : "var(--border)"
            },
            children: "▶"
        }, void 0, false, {
            fileName: "[project]/afm-frontend/app/page.tsx",
            lineNumber: 1542,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1532,
        columnNumber: 5
    }, this);
}
function ImageFrame({ src, caption, height = 190 }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        style: {
            border: "1px solid var(--border)",
            borderRadius: 4,
            overflow: "hidden",
            background: "#000"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    width: "100%",
                    minHeight: height,
                    background: "#000",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                },
                children: src ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("img", {
                    src: src,
                    alt: caption,
                    style: {
                        width: "100%",
                        height,
                        objectFit: "contain",
                        display: "block",
                        background: "#000"
                    }
                }, void 0, false, {
                    fileName: "[project]/afm-frontend/app/page.tsx",
                    lineNumber: 1586,
                    columnNumber: 11
                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    style: {
                        color: "var(--muted)",
                        fontSize: "0.72rem"
                    },
                    children: "No preview available"
                }, void 0, false, {
                    fileName: "[project]/afm-frontend/app/page.tsx",
                    lineNumber: 1598,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1575,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: {
                    fontSize: "0.65rem",
                    padding: "4px 10px",
                    background: "var(--surface2)",
                    borderTop: "1px solid var(--border)",
                    color: "var(--muted)"
                },
                children: caption
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1603,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1567,
        columnNumber: 5
    }, this);
}
function ResultsImage({ label, src, caption }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                style: smallLabelStyle,
                children: label
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1629,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(ImageFrame, {
                src: src,
                caption: caption,
                height: 160
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1630,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1628,
        columnNumber: 5
    }, this);
}
function RadioOption({ active, accent, onClick, label, icon }) {
    const borderColor = active ? accent === "green" ? "var(--green)" : "var(--accent)" : "var(--border)";
    const color = active ? accent === "green" ? "var(--green)" : "var(--accent)" : "var(--text)";
    const background = active ? accent === "green" ? "rgba(0,255,157,0.05)" : "rgba(0,212,255,0.05)" : "var(--surface2)";
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        onClick: onClick,
        style: {
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
            color
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                children: icon
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1683,
                columnNumber: 7
            }, this),
            label
        ]
    }, void 0, true, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1667,
        columnNumber: 5
    }, this);
}
function JobRow({ label, value }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
        style: {
            borderBottom: "1px solid var(--border)"
        },
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                style: {
                    padding: "7px 0",
                    color: "var(--muted)",
                    textTransform: "uppercase",
                    fontSize: "0.68rem",
                    letterSpacing: "0.06em"
                },
                children: label
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1692,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$afm$2d$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                style: {
                    padding: "7px 0",
                    color: "var(--text)",
                    fontSize: "0.68rem",
                    textAlign: "right",
                    wordBreak: "break-word"
                },
                children: value
            }, void 0, false, {
                fileName: "[project]/afm-frontend/app/page.tsx",
                lineNumber: 1703,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/afm-frontend/app/page.tsx",
        lineNumber: 1691,
        columnNumber: 5
    }, this);
}
const smallLabelStyle = {
    fontSize: "0.65rem",
    textTransform: "uppercase",
    letterSpacing: "0.1em",
    color: "var(--muted)",
    marginBottom: 5,
    fontWeight: 700
};
const runButtonStyle = {
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
    boxShadow: "0 0 20px rgba(0,212,255,0.25)"
};
const secondaryLargeButtonStyle = {
    background: "var(--surface2)",
    boxShadow: "none",
    border: "1px solid var(--border)",
    color: "var(--muted)",
    borderRadius: 5,
    padding: "9px 20px",
    fontSize: "0.82rem",
    fontWeight: 700,
    cursor: "pointer"
};
const secondaryButtonStyle = {
    background: "var(--surface2)",
    border: "1px solid var(--border)",
    color: "var(--muted)",
    padding: "6px 14px",
    borderRadius: 4,
    fontSize: "0.73rem",
    cursor: "pointer"
};
const tabButtonStyle = (active)=>({
        padding: "6px 16px",
        background: active ? "rgba(0,212,255,0.1)" : "var(--surface)",
        border: active ? "1px solid var(--accent)" : "1px solid var(--border)",
        borderRadius: 4,
        fontSize: "0.73rem",
        color: active ? "var(--accent)" : "var(--muted)",
        cursor: "pointer"
    });
const toolButtonStyle = (active)=>({
        background: active ? "rgba(0,212,255,0.12)" : "var(--surface2)",
        border: active ? "1px solid var(--accent)" : "1px solid var(--border)",
        color: active ? "var(--accent)" : "var(--muted)",
        padding: "6px 14px",
        borderRadius: 4,
        fontSize: "0.73rem",
        cursor: "pointer",
        boxShadow: active ? "0 0 8px rgba(0,212,255,0.15)" : "none"
    });
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__8ab5dec6._.js.map