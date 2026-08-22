import { Copy, Pencil, Plus, WalletCards } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  createDepositWallet,
  listDepositWallets,
  updateDepositWallet,
} from "../api/depositWallets";
import type { DepositWallet, DepositWalletInput } from "../api/types";
import { Button } from "../components/Button";
import { DataTable } from "../components/DataTable";
import { EmptyState } from "../components/EmptyState";
import { FormField } from "../components/FormField";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/StatusBadge";
import { Toast } from "../components/Toast";
import { formatDateTime } from "../utils/date";

const USDT_ETHEREUM_CONTRACT =
  "0xdac17f958d2ee523a2206206994597c13d831ec7";

const initialForm: DepositWalletInput = {
  title: "",
  address: "",
  asset: "USDT",
  network: "ETHEREUM",
  network_display_name: "Ethereum (ERC-20)",
  provider: "infura",
  provider_network: "mainnet",
  chain_id: 1,
  token_standard: "ERC20",
  token_contract_address: USDT_ETHEREUM_CONTRACT,
  token_decimals: 6,
  confirmations_required: 12,
  monitoring_enabled: true,
  sort_order: 0,
  is_active: true,
};

function toForm(wallet: DepositWallet): DepositWalletInput {
  return {
    title: wallet.title,
    address: wallet.address,
    asset: wallet.asset,
    network: wallet.network,
    network_display_name: wallet.network_display_name,
    provider: wallet.provider,
    provider_network: wallet.provider_network,
    chain_id: wallet.chain_id,
    token_standard: wallet.token_standard,
    token_contract_address: wallet.token_contract_address,
    token_decimals: wallet.token_decimals,
    confirmations_required: wallet.confirmations_required,
    monitoring_enabled: wallet.monitoring_enabled,
    sort_order: wallet.sort_order,
    is_active: wallet.is_active,
  };
}

export function DepositWalletsPage() {
  const [items, setItems] = useState<DepositWallet[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<DepositWallet | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<DepositWalletInput>(initialForm);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    listDepositWallets(1, 100)
      .then((response) => setItems(response.items))
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  function set<K extends keyof DepositWalletInput>(
    key: K,
    value: DepositWalletInput[K],
  ) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function setAutomaticMonitoring(enabled: boolean) {
    setForm((current) =>
      enabled
        ? {
            ...current,
            asset: "USDT",
            network: "ETHEREUM",
            network_display_name: "Ethereum (ERC-20)",
            provider: "infura",
            provider_network: "mainnet",
            chain_id: 1,
            token_standard: "ERC20",
            token_contract_address: USDT_ETHEREUM_CONTRACT,
            token_decimals: 6,
            confirmations_required: current.confirmations_required || 12,
            monitoring_enabled: true,
          }
        : {
            ...current,
            provider: "manual",
            provider_network: null,
            chain_id: null,
            token_standard: null,
            token_contract_address: null,
            monitoring_enabled: false,
          },
    );
  }

  function openCreate() {
    setEditing(null);
    setForm({ ...initialForm });
    setError("");
    setModalOpen(true);
  }

  function openEdit(wallet: DepositWallet) {
    setEditing(wallet);
    setForm(toForm(wallet));
    setError("");
    setModalOpen(true);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (editing) {
        await updateDepositWallet(editing.id, form);
        setMessage("Адрес пополнения обновлён");
      } else {
        await createDepositWallet(form);
        setMessage("Адрес пополнения добавлен");
      }
      setModalOpen(false);
      load();
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Не удалось сохранить адрес",
      );
    } finally {
      setBusy(false);
    }
  }

  async function toggle(wallet: DepositWallet) {
    setError("");
    try {
      await updateDepositWallet(wallet.id, { is_active: !wallet.is_active });
      setMessage(
        wallet.is_active
          ? "Адрес отключён для новых пополнений"
          : "Адрес снова доступен для пополнений",
      );
      load();
    } catch (toggleError) {
      setError(
        toggleError instanceof Error
          ? toggleError.message
          : "Не удалось изменить статус",
      );
    }
  }

  async function copyAddress(address: string) {
    try {
      await navigator.clipboard.writeText(address);
      setMessage("Адрес скопирован");
    } catch {
      setError("Не удалось скопировать адрес");
    }
  }

  return (
    <>
      <PageHeader
        title="Адреса пополнения"
        description="Добавляйте адреса разных сетей. Автоматическая проверка сейчас доступна для USDT ERC-20 в Ethereum через Infura."
        actions={
          <Button onClick={openCreate}>
            <Plus />
            Добавить адрес
          </Button>
        }
      />

      {message && <Toast message={message} />}
      {error && !modalOpen && <Toast message={error} type="error" />}

      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <EmptyState
          title="Адресов пока нет"
          description="Добавьте первый адрес, чтобы пользователи могли создавать заявки на пополнение."
        />
      ) : (
        <DataTable label="Адреса пополнения">
          <thead>
            <tr>
              <th>Название</th>
              <th>Адрес</th>
              <th>Сеть</th>
              <th>Проверка</th>
              <th>Статус</th>
              <th>Изменено</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((wallet) => (
              <tr key={wallet.id}>
                <td>
                  <strong>{wallet.title}</strong>
                  <small>{wallet.asset}</small>
                </td>
                <td>
                  <code className="wallet-address-code">{wallet.address}</code>
                </td>
                <td>
                  <strong>{wallet.network_display_name}</strong>
                  <small>{wallet.network}</small>
                </td>
                <td>
                  <strong>
                    {wallet.monitoring_enabled ? "Автоматическая" : "Ручная"}
                  </strong>
                  <small>
                    {wallet.monitoring_enabled
                      ? `${wallet.provider} · ${wallet.provider_network ?? "—"}`
                      : "Без провайдера"}
                  </small>
                </td>
                <td>
                  <StatusBadge
                    value={wallet.is_active ? "active" : "inactive"}
                  />
                </td>
                <td>{formatDateTime(wallet.updated_at)}</td>
                <td className="row-actions">
                  <Button
                    type="button"
                    variant="ghost"
                    aria-label="Скопировать адрес"
                    onClick={() => copyAddress(wallet.address)}
                  >
                    <Copy />
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => openEdit(wallet)}
                  >
                    <Pencil />
                    Изменить
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => toggle(wallet)}
                  >
                    {wallet.is_active ? "Отключить" : "Включить"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}

      <Modal
        open={modalOpen}
        title={editing ? "Изменить адрес" : "Новый адрес пополнения"}
        onClose={() => !busy && setModalOpen(false)}
      >
        <form onSubmit={submit}>
          <div className="wallet-form-heading">
            <WalletCards />
            <p>
              Для произвольной сети отключите автоматическую проверку. Для такой
              сети автоматическая проверка не выполняется; перевод проверяется
              администратором.
            </p>
          </div>
          <FormField label="Название" hint="Например: Основной Ethereum кошелёк">
            <input
              value={form.title}
              onChange={(event) => set("title", event.target.value)}
              minLength={2}
              maxLength={120}
              required
            />
          </FormField>
          <FormField label="Адрес кошелька">
            <input
              value={form.address}
              onChange={(event) => set("address", event.target.value.trim())}
              placeholder={form.monitoring_enabled ? "0x..." : "Адрес выбранной сети"}
              autoComplete="off"
              required
            />
          </FormField>
          <div className="form-grid">
            <FormField label="Актив">
              <input
                value={form.asset}
                onChange={(event) => set("asset", event.target.value.toUpperCase())}
                readOnly
                required
              />
            </FormField>
            <FormField label="Код сети">
              <input
                value={form.network}
                onChange={(event) => set("network", event.target.value.toUpperCase())}
                readOnly={form.monitoring_enabled}
                required
              />
            </FormField>
            <FormField label="Название сети для пользователей">
              <input
                value={form.network_display_name}
                onChange={(event) =>
                  set("network_display_name", event.target.value)
                }
                readOnly={form.monitoring_enabled}
                required
              />
            </FormField>
            <FormField label="Порядок отображения">
              <input
                type="number"
                min="0"
                max="10000"
                value={form.sort_order}
                onChange={(event) =>
                  set("sort_order", event.currentTarget.valueAsNumber)
                }
                required
              />
            </FormField>
          </div>

          <label className="checkbox">
            <input
              type="checkbox"
              checked={form.monitoring_enabled}
              onChange={(event) => setAutomaticMonitoring(event.target.checked)}
            />
            Проверять входящие переводы автоматически
          </label>

          {form.monitoring_enabled && (
            <div className="form-grid">
              <FormField label="Провайдер">
                <select
                  value={form.provider}
                  onChange={(event) => set("provider", event.target.value)}
                  disabled
                >
                  <option value="infura">Infura</option>
                </select>
              </FormField>
              <FormField label="Сеть Infura" hint="Для Ethereum Mainnet: mainnet">
                <input
                  value={form.provider_network ?? ""}
                  onChange={(event) =>
                    set("provider_network", event.target.value || null)
                  }
                  readOnly
                  required
                />
              </FormField>
              <FormField label="Chain ID">
                <input
                  type="number"
                  min="1"
                  value={form.chain_id ?? ""}
                  onChange={(event) =>
                    set(
                      "chain_id",
                      event.currentTarget.value
                        ? event.currentTarget.valueAsNumber
                        : null,
                    )
                  }
                  readOnly
                  required
                />
              </FormField>
              <FormField label="Стандарт токена">
                <input
                  value={form.token_standard ?? ""}
                  onChange={(event) =>
                    set("token_standard", event.target.value.toUpperCase() || null)
                  }
                  readOnly
                  required
                />
              </FormField>
              <FormField label="Контракт токена">
                <input
                  value={form.token_contract_address ?? ""}
                  onChange={(event) =>
                    set(
                      "token_contract_address",
                      event.target.value.trim() || null,
                    )
                  }
                  readOnly
                  required
                />
              </FormField>
              <FormField label="Знаков токена">
                <input
                  type="number"
                  min="0"
                  max="18"
                  value={form.token_decimals}
                  onChange={(event) =>
                    set("token_decimals", event.currentTarget.valueAsNumber)
                  }
                  readOnly
                  required
                />
              </FormField>
              <FormField label="Подтверждений">
                <input
                  type="number"
                  min="1"
                  value={form.confirmations_required}
                  onChange={(event) =>
                    set(
                      "confirmations_required",
                      event.currentTarget.valueAsNumber,
                    )
                  }
                  required
                />
              </FormField>
            </div>
          )}

          <label className="checkbox">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => set("is_active", event.target.checked)}
            />
            Показывать этот адрес пользователям
          </label>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          <div className="form-actions">
            <Button
              type="button"
              variant="secondary"
              disabled={busy}
              onClick={() => setModalOpen(false)}
            >
              Отмена
            </Button>
            <Button type="submit" loading={busy}>
              Сохранить
            </Button>
          </div>
        </form>
      </Modal>
    </>
  );
}
