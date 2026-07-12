import { trackApiRequest, captureError } from "@/lib/monitor";

const API_URL = process.env.API_URL || "http://localhost:8000";
const API_SECRET = process.env.API_SECRET || "";

type FetchOptions = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  cache?: RequestCache;
  retry?: number; // 重试次数，默认 0
  timeout?: number; // 超时时间（毫秒），默认 30000
};

/** 统一 API 错误格式（与后端 error_response 对应） */
export interface ApiError {
  code: string;
  message: string;
  detail?: unknown;
}

/** 统一 API 响应格式（与后端 error_response 对应） */
export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  meta: { timestamp: string };
}

type ApiResult<T> = {
  ok: boolean;
  status: number;
  data: T | null;
  error: string | null;
};

/**
 * 统一的 API 错误消息映射
 */
function getErrorMessage(status: number, statusText: string): string {
  switch (status) {
    case 401:
      return "未授权，请重新登录";
    case 403:
      return "权限不足，无法访问";
    case 404:
      return "请求的资源不存在";
    case 500:
      return "服务器错误，请稍后重试";
    case 502:
      return "网关错误，请稍后重试";
    case 503:
      return "服务暂时不可用，请稍后重试";
    case 504:
      return "网关超时，请稍后重试";
    default:
      return statusText || `请求失败 (${status})`;
  }
}

/**
 * 带超时的 fetch 封装
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * 统一的 API 请求函数
 *
 * @param path - API 路径
 * @param options - 请求选项
 * @param options.method - HTTP 方法，默认 GET
 * @param options.body - 请求体
 * @param options.headers - 额外请求头
 * @param options.cache - 缓存策略
 * @param options.retry - 重试次数，默认 0
 * @param options.timeout - 超时时间（毫秒），默认 30000
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {}
): Promise<ApiResult<T>> {
  const startTime = Date.now();
  const {
    method = "GET",
    body,
    headers = {},
    cache,
    retry = 0,
    timeout = 30000,
  } = options;

  const fetchHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    ...headers,
  };
  if (API_SECRET) {
    fetchHeaders["X-API-Key"] = API_SECRET;
  }

  const requestOptions: RequestInit = {
    method,
    headers: fetchHeaders,
    body: body ? JSON.stringify(body) : undefined,
    cache,
  };

  let lastError: string = "";
  let attempts = 0;
  let finalStatus = 0;
  const maxAttempts = retry + 1;

  while (attempts < maxAttempts) {
    attempts++;

    try {
      const res = await fetchWithTimeout(
        `${API_URL}${path}`,
        requestOptions,
        timeout
      );
      finalStatus = res.status;

      if (res.ok) {
        try {
          const data = await res.json();
          trackApiRequest(path, method, res.status, Date.now() - startTime);
          return { ok: true, status: res.status, data, error: null };
        } catch (parseError) {
          const errorMsg = "响应数据解析失败";
          captureError(parseError as Error, { path, method, status: res.status });
          trackApiRequest(path, method, res.status, Date.now() - startTime, errorMsg);
          return {
            ok: false,
            status: res.status,
            data: null,
            error: errorMsg,
          };
        }
      }

      let errorData: {
        message?: string;
        error?: string | { code?: string; message?: string };
        detail?: string;
        code?: string;
      } | null = null;
      try {
        errorData = await res.json();
      } catch {
      }

      const unifiedError =
        errorData?.error && typeof errorData.error === "object"
          ? errorData.error
          : null;
      const errorMessage =
        unifiedError?.message ||
        errorData?.message ||
        (typeof errorData?.error === "string" ? errorData.error : undefined) ||
        errorData?.detail ||
        getErrorMessage(res.status, res.statusText);

      if (res.status >= 400 && res.status < 500) {
        trackApiRequest(path, method, res.status, Date.now() - startTime, errorMessage);
        return { ok: false, status: res.status, data: null, error: errorMessage };
      }

      lastError = errorMessage;
    } catch (err) {
      if (err instanceof Error) {
        if (err.name === "AbortError") {
          lastError = "请求超时，请检查网络连接";
        } else {
          lastError = "网络错误，请检查连接";
        }
      } else {
        lastError = "网络错误，请检查连接";
      }
    }

    if (attempts < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, 1000 * attempts));
    }
  }

  const duration = Date.now() - startTime;
  trackApiRequest(path, method, finalStatus, duration, lastError);
  captureError(lastError, { path, method, status: finalStatus, duration });
  return { ok: false, status: finalStatus, data: null, error: lastError };
}

/**
 * 便捷的 GET 请求方法
 */
export async function apiGet<T = unknown>(
  path: string,
  options?: Omit<FetchOptions, "method" | "body">
): Promise<ApiResult<T>> {
  return apiFetch<T>(path, { ...options, method: "GET" });
}

/**
 * 便捷的 POST 请求方法
 */
export async function apiPost<T = unknown>(
  path: string,
  body: unknown,
  options?: Omit<FetchOptions, "method" | "body">
): Promise<ApiResult<T>> {
  return apiFetch<T>(path, { ...options, method: "POST", body });
}

/**
 * 便捷的 PUT 请求方法
 */
export async function apiPut<T = unknown>(
  path: string,
  body: unknown,
  options?: Omit<FetchOptions, "method" | "body">
): Promise<ApiResult<T>> {
  return apiFetch<T>(path, { ...options, method: "PUT", body });
}

/**
 * 便捷的 DELETE 请求方法
 */
export async function apiDelete<T = unknown>(
  path: string,
  options?: Omit<FetchOptions, "method">
): Promise<ApiResult<T>> {
  return apiFetch<T>(path, { ...options, method: "DELETE" });
}
