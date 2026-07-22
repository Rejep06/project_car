import { apiRequest } from "./client";
import type { Pagination, Post, PostInput } from "./types";
export const listPosts = (page = 1, pageSize = 20) =>
  apiRequest<Pagination<Post>>(
    `/admin/posts?page=${page}&page_size=${pageSize}`,
  );
export const getPost = (id: string) => apiRequest<Post>(`/admin/posts/${id}`);
export const createPost = (data: PostInput) =>
  apiRequest<Post>("/admin/posts", {
    method: "POST",
    body: JSON.stringify(data),
  });
export const updatePost = (id: string, data: Partial<PostInput>) =>
  apiRequest<Post>(`/admin/posts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
export const publishPost = (id: string) =>
  apiRequest<Post>(`/admin/posts/${id}/publish`, { method: "POST" });
export const archivePost = (id: string) =>
  apiRequest<Post>(`/admin/posts/${id}/archive`, { method: "POST" });
