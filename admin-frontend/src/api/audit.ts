import { apiRequest } from "./client";
import type { AuditLog, Pagination } from "./types";
export const listAudit = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<AuditLog>>(
    `/admin/audit-logs?page=${page}&page_size=${pageSize}`,
  );
