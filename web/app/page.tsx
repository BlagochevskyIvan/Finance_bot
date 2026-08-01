"use client";

import { useCallback, useEffect, useState } from "react";

import { getTelegramWebApp, type TelegramUser } from "@/lib/telegram";

type ApiState = "loading" | "online" | "offline";

type Profile = {
  first_name: string | null;
  username: string | null;
};

function displayName(user?: TelegramUser, profile?: Profile | null): string {
  return profile?.first_name || user?.first_name || user?.username || "друг";
}

export default function Home() {
  const [apiState, setApiState] = useState<ApiState>("loading");
  const [telegramUser, setTelegramUser] = useState<TelegramUser>();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [message, setMessage] = useState("Проверяем подключение к сервисам");

  const checkConnection = useCallback(async () => {
    setApiState("loading");
    setMessage("Проверяем подключение к сервисам");

    try {
      const healthResponse = await fetch("/api/health", { cache: "no-store" });
      if (!healthResponse.ok) {
        throw new Error("API is unavailable");
      }

      const webApp = getTelegramWebApp();
      const currentUser = webApp?.initDataUnsafe?.user;
      setTelegramUser(currentUser);

      if (webApp?.initData) {
        const profileResponse = await fetch("/api/me", {
          cache: "no-store",
          headers: { "X-Telegram-Auth": webApp.initData },
        });
        if (!profileResponse.ok) {
          throw new Error("Telegram authorization failed");
        }
        setProfile((await profileResponse.json()) as Profile);
        setMessage("Telegram и база данных подключены");
      } else {
        setMessage("API работает. Откройте страницу из Telegram для авторизации");
      }

      setApiState("online");
    } catch {
      setApiState("offline");
      setMessage("Сервис пока недоступен. Попробуйте ещё раз");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void checkConnection();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [checkConnection]);

  return (
    <main className="shell">
      <section className="appCard" aria-labelledby="page-title">
        <header className="topbar">
          <div className="brand">
            <span className="brandMark" aria-hidden="true">B</span>
            <span>BASE MINI APP</span>
          </div>
          <span className={"statusPill " + apiState}>
            <span className="statusDot" aria-hidden="true" />
            {apiState === "loading" ? "Проверка" : apiState === "online" ? "Онлайн" : "Офлайн"}
          </span>
        </header>

        <div className="hero">
          <p className="eyebrow">ГЛАВНАЯ СТРАНИЦА</p>
          <h1 id="page-title">Привет, {displayName(telegramUser, profile)}.</h1>
          <p className="lead">
            Каркас готов. Здесь можно собирать сценарии вашего бота,
            не меняя базовую инфраструктуру.
          </p>
        </div>

        <div className="systemCard">
          <div className="systemIcon" aria-hidden="true">
            <span />
          </div>
          <div>
            <p className="systemLabel">Состояние системы</p>
            <p className="systemMessage" aria-live="polite">{message}</p>
          </div>
        </div>

        <div className="steps" aria-label="Подключённые части приложения">
          <article>
            <span>01</span>
            <div>
              <h2>Mini App</h2>
              <p>Одна адаптивная страница</p>
            </div>
          </article>
          <article>
            <span>02</span>
            <div>
              <h2>FastAPI</h2>
              <p>API и Telegram webhook</p>
            </div>
          </article>
          <article>
            <span>03</span>
            <div>
              <h2>PostgreSQL</h2>
              <p>Пользователь сохраняется автоматически</p>
            </div>
          </article>
        </div>

        <button
          className="primaryButton"
          type="button"
          onClick={() => void checkConnection()}
          disabled={apiState === "loading"}
        >
          {apiState === "loading" ? "Проверяем…" : "Проверить подключение"}
          <span aria-hidden="true">↗</span>
        </button>

        <footer>
          <span>Telegram-ready</span>
          <span className="footerLine" />
          <span>v0.1</span>
        </footer>
      </section>
    </main>
  );
}
