/**
 * Offline Cache Helper (CHUNK 7.9)
 * Browser-side caching using LocalForage (IndexedDB wrapper)
 */

// Check if localforage is available
let localforage = null;

try {
    if (typeof require !== 'undefined') {
        localforage = require('localforage');
    } else if (typeof window !== 'undefined' && window.localforage) {
        localforage = window.localforage;
    }
} catch (e) {
    console.warn('localforage not available, using localStorage fallback');
}

// Fallback to localStorage if localforage unavailable
const useLocalStorage = !localforage;

/**
 * Save data to offline cache
 */
async function saveToCache(key, value) {
    try {
        if (useLocalStorage) {
            localStorage.setItem(`aether_cache_${key}`, JSON.stringify(value));
            return true;
        } else {
            await localforage.setItem(key, value);
            return true;
        }
    } catch (error) {
        console.error('Error saving to cache:', error);
        return false;
    }
}

/**
 * Load data from offline cache
 */
async function loadFromCache(key) {
    try {
        if (useLocalStorage) {
            const item = localStorage.getItem(`aether_cache_${key}`);
            return item ? JSON.parse(item) : null;
        } else {
            return await localforage.getItem(key);
        }
    } catch (error) {
        console.error('Error loading from cache:', error);
        return null;
    }
}

/**
 * Clear cache entry
 */
async function clearCache(key) {
    try {
        if (useLocalStorage) {
            localStorage.removeItem(`aether_cache_${key}`);
            return true;
        } else {
            await localforage.removeItem(key);
            return true;
        }
    } catch (error) {
        console.error('Error clearing cache:', error);
        return false;
    }
}

/**
 * Clear all cache
 */
async function clearAllCache() {
    try {
        if (useLocalStorage) {
            const keys = Object.keys(localStorage).filter(k => k.startsWith('aether_cache_'));
            keys.forEach(key => localStorage.removeItem(key));
            return true;
        } else {
            await localforage.clear();
            return true;
        }
    } catch (error) {
        console.error('Error clearing all cache:', error);
        return false;
    }
}

/**
 * Get cache size estimate
 */
async function getCacheSize() {
    try {
        if (useLocalStorage) {
            const keys = Object.keys(localStorage).filter(k => k.startsWith('aether_cache_'));
            let totalSize = 0;
            keys.forEach(key => {
                const item = localStorage.getItem(key);
                totalSize += item ? item.length : 0;
            });
            return totalSize;
        } else {
            // LocalForage doesn't provide size directly
            const keys = await localforage.keys();
            return keys.length; // Return key count as proxy
        }
    } catch (error) {
        console.error('Error getting cache size:', error);
        return 0;
    }
}

// Export functions for use in browser
if (typeof window !== 'undefined') {
    window.aetherOfflineCache = {
        save: saveToCache,
        load: loadFromCache,
        clear: clearCache,
        clearAll: clearAllCache,
        getSize: getCacheSize
    };
}

// Export for Node/CommonJS if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        saveToCache,
        loadFromCache,
        clearCache,
        clearAllCache,
        getCacheSize
    };
}

