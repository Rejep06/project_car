import { apiRequest } from "./client";
import type { Pagination, Post } from "./types";

export const listPosts = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<Post>>(`/posts?page=${page}&page_size=${pageSize}`, {
    skipAuth: true,
  });
export const getPost = (slug: string) =>
  apiRequest<Post>(`/posts/${encodeURIComponent(slug)}`, { skipAuth: true });
