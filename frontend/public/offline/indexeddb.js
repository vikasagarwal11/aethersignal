/**
 * IndexedDB Storage Layer (CHUNK B1)
 * Browser database for offline data storage.
 * Stores: uploaded CSV/FAERS files, normalized data, trend outputs, governance artifacts.
 */

const DB_NAME = "aether_signal";
const DB_VERSION = 1;
let db = null;

/**
 * Open IndexedDB database.
 * @returns {Promise<IDBDatabase>}
 */
function openDB() {
    return new Promise((resolve, reject) => {
        if (db) {
            resolve(db);
            return;
        }

        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (event) => {
            db = event.target.result;

            // Create object stores if they don't exist
            if (!db.objectStoreNames.contains("datasets")) {
                db.createObjectStore("datasets", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("summaries")) {
                db.createObjectStore("summaries", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("governance")) {
                db.createObjectStore("governance", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("trend_alerts")) {
                db.createObjectStore("trend_alerts", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("rpf_scores")) {
                db.createObjectStore("rpf_scores", { keyPath: "id" });
            }
            if (!db.objectStoreNames.contains("cache")) {
                db.createObjectStore("cache", { keyPath: "key" });
            }
        };

        request.onsuccess = () => {
            db = request.result;
            resolve(db);
        };

        request.onerror = () => {
            reject(new Error("IndexedDB Failed: " + request.error));
        };
    });
}

/**
 * Save dataset to IndexedDB.
 * @param {string} id - Dataset identifier
 * @param {any} data - Dataset data (can be any serializable object)
 * @returns {Promise<void>}
 */
export async function saveDataset(id, data) {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("datasets", "readwrite");
            const store = tx.objectStore("datasets");
            const request = store.put({ id, data, timestamp: Date.now() });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error saving dataset:", error);
        throw error;
    }
}

/**
 * Load dataset from IndexedDB.
 * @param {string} id - Dataset identifier
 * @returns {Promise<any|null>}
 */
export async function loadDataset(id) {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("datasets", "readonly");
            const store = tx.objectStore("datasets");
            const request = store.get(id);
            
            request.onsuccess = () => {
                resolve(request.result?.data || null);
            };
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error loading dataset:", error);
        return null;
    }
}

/**
 * Save summary to IndexedDB.
 * @param {string} id - Summary identifier
 * @param {any} data - Summary data
 * @returns {Promise<void>}
 */
export async function saveSummary(id, data) {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("summaries", "readwrite");
            const store = tx.objectStore("summaries");
            const request = store.put({ id, data, timestamp: Date.now() });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error saving summary:", error);
        throw error;
    }
}

/**
 * Load summary from IndexedDB.
 * @param {string} id - Summary identifier
 * @returns {Promise<any|null>}
 */
export async function loadSummary(id) {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("summaries", "readonly");
            const store = tx.objectStore("summaries");
            const request = store.get(id);
            
            request.onsuccess = () => {
                resolve(request.result?.data || null);
            };
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error loading summary:", error);
        return null;
    }
}

/**
 * Save governance artifact to IndexedDB.
 * @param {string} id - Governance artifact identifier
 * @param {any} data - Governance data
 * @returns {Promise<void>}
 */
export async function saveGovernance(id, data) {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("governance", "readwrite");
            const store = tx.objectStore("governance");
            const request = store.put({ id, data, timestamp: Date.now() });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error saving governance:", error);
        throw error;
    }
}

/**
 * Load governance artifact from IndexedDB.
 * @param {string} id - Governance artifact identifier
 * @returns {Promise<any|null>}
 */
export async function loadGovernance(id) {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("governance", "readonly");
            const store = tx.objectStore("governance");
            const request = store.get(id);
            
            request.onsuccess = () => {
                resolve(request.result?.data || null);
            };
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error loading governance:", error);
        return null;
    }
}

/**
 * Clear all data from IndexedDB.
 * @returns {Promise<void>}
 */
export async function clearAllData() {
    try {
        await openDB();
        const objectStores = ["datasets", "summaries", "governance", "trend_alerts", "rpf_scores", "cache"];
        
        for (const storeName of objectStores) {
            await new Promise((resolve, reject) => {
                const tx = db.transaction(storeName, "readwrite");
                const store = tx.objectStore(storeName);
                const request = store.clear();
                
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        }
    } catch (error) {
        console.error("Error clearing data:", error);
        throw error;
    }
}

/**
 * Get all dataset IDs stored in IndexedDB.
 * @returns {Promise<string[]>}
 */
export async function listDatasetIds() {
    try {
        await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction("datasets", "readonly");
            const store = tx.objectStore("datasets");
            const request = store.getAllKeys();
            
            request.onsuccess = () => {
                resolve(request.result || []);
            };
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error("Error listing datasets:", error);
        return [];
    }
}

