const accessKey = "automotive_customer_access_token";
const refreshKey = "automotive_customer_refresh_token";

function readToken(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeToken(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // При недоступном localStorage сессия сохранится только до обновления страницы.
  }
}

function removeToken(key: string): void {
  try {
    localStorage.removeItem(key);
  } catch {
    // Нечего дополнительно очищать.
  }
}

export const tokenStore = {
  getAccessToken: () => readToken(accessKey),
  getRefreshToken: () => readToken(refreshKey),
  setTokens: (access: string, refresh: string) => {
    // Access записывается первым: другая вкладка увидит новую пару целиком.
    writeToken(accessKey, access);
    writeToken(refreshKey, refresh);
  },
  setAccessToken: (access: string) => {
    writeToken(accessKey, access);
  },
  clear: () => {
    removeToken(accessKey);
    removeToken(refreshKey);
  },
};
