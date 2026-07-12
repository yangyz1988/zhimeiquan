const isDevelopment = process.env.NODE_ENV === "development";

interface MonitorEvent {
  type: "error" | "api" | "performance" | "warning";
  message: string;
  timestamp: number;
  details?: Record<string, unknown>;
}

interface ApiRequestInfo {
  url: string;
  method: string;
  status: number;
  duration: number;
  success: boolean;
  error?: string;
}

interface PerformanceMetric {
  name: string;
  value: number;
  unit: "ms" | "bytes" | "count";
}

const monitorEvents: MonitorEvent[] = [];
const apiRequests: ApiRequestInfo[] = [];
const performanceMetrics: PerformanceMetric[] = [];

const MAX_EVENTS = 1000;
const MAX_API_REQUESTS = 500;
const MAX_METRICS = 100;

function trimArray<T>(arr: T[], maxSize: number): void {
  while (arr.length > maxSize) {
    arr.shift();
  }
}

export function captureError(error: Error | string, details?: Record<string, unknown>): void {
  const event: MonitorEvent = {
    type: "error",
    message: typeof error === "string" ? error : error.message,
    timestamp: Date.now(),
    details: {
      stack: typeof error === "object" ? error.stack : undefined,
      ...details,
    },
  };

  monitorEvents.push(event);
  trimArray(monitorEvents, MAX_EVENTS);

  if (isDevelopment) {
    console.error("[Monitor] Error captured:", event);
  }
}

export function captureWarning(message: string, details?: Record<string, unknown>): void {
  const event: MonitorEvent = {
    type: "warning",
    message,
    timestamp: Date.now(),
    details,
  };

  monitorEvents.push(event);
  trimArray(monitorEvents, MAX_EVENTS);

  if (isDevelopment) {
    console.warn("[Monitor] Warning captured:", event);
  }
}

export function trackApiRequest(
  url: string,
  method: string,
  status: number,
  duration: number,
  error?: string
): void {
  const request: ApiRequestInfo = {
    url,
    method,
    status,
    duration,
    success: status >= 200 && status < 300,
    error,
  };

  apiRequests.push(request);
  trimArray(apiRequests, MAX_API_REQUESTS);

  if (isDevelopment) {
    if (request.success) {
      console.info("[Monitor] API Request:", `${method} ${url} ${status} ${duration}ms`);
    } else {
      console.error("[Monitor] API Error:", `${method} ${url} ${status} ${duration}ms`, error);
    }
  }
}

export function trackPerformance(name: string, value: number, unit: "ms" | "bytes" | "count"): void {
  const metric: PerformanceMetric = { name, value, unit };
  performanceMetrics.push(metric);
  trimArray(performanceMetrics, MAX_METRICS);

  if (isDevelopment) {
    console.info(`[Monitor] Performance: ${name} = ${value}${unit}`);
  }
}

export function getMonitorState() {
  const errorCount = monitorEvents.filter((e) => e.type === "error").length;
  const warningCount = monitorEvents.filter((e) => e.type === "warning").length;
  const recentErrors = monitorEvents
    .filter((e) => e.type === "error")
    .slice(-10)
    .reverse();
  const recentApiRequests = apiRequests.slice(-20).reverse();

  const apiSummary = {
    total: apiRequests.length,
    success: apiRequests.filter((r) => r.success).length,
    failure: apiRequests.filter((r) => !r.success).length,
    avgDuration: apiRequests.length
      ? Math.round(apiRequests.reduce((sum, r) => sum + r.duration, 0) / apiRequests.length)
      : 0,
    p95Duration: apiRequests.length
      ? Math.round(
          [...apiRequests]
            .sort((a, b) => a.duration - b.duration)
            [Math.floor(apiRequests.length * 0.95)]?.duration || 0
        )
      : 0,
  };

  return {
    errors: {
      count: errorCount,
      recent: recentErrors,
    },
    warnings: {
      count: warningCount,
    },
    api: {
      ...apiSummary,
      recent: recentApiRequests,
    },
    performance: performanceMetrics.slice(-20).reverse(),
  };
}

export function clearMonitorData(): void {
  monitorEvents.length = 0;
  apiRequests.length = 0;
  performanceMetrics.length = 0;
}

export function initFrontendMonitoring(): void {
  window.addEventListener("error", (event) => {
    captureError(event.error || new Error(event.message), {
      source: event.filename,
      line: event.lineno,
      column: event.colno,
    });
  });

  window.addEventListener("unhandledrejection", (event) => {
    captureError(event.reason || new Error("Unhandled promise rejection"), {
      type: "unhandled_rejection",
    });
  });

  if (typeof window !== "undefined" && (window as any).performance?.mark) {
    const handleLoad = () => {
      const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming;
      if (navigation) {
        trackPerformance("ttfb", Math.round(navigation.responseStart), "ms");
        trackPerformance("fcp", Math.round(navigation.domContentLoadedEventStart), "ms");
        trackPerformance("load", Math.round(navigation.loadEventStart), "ms");
      }
    };

    if (document.readyState === "complete") {
      handleLoad();
    } else {
      window.addEventListener("load", handleLoad);
    }
  }

  if (isDevelopment) {
    console.info("[Monitor] Frontend monitoring initialized");
  }
}