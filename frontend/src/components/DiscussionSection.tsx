"use client";

import { useState, useEffect, useCallback } from "react";
import { isLoggedIn } from "@/lib/auth";
import { discussionsApi } from "@/lib/queries";
import { addToast } from "@/lib/toast";
import type { DiscussionItem, CommentItem } from "@/types";

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diff = now - date;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "방금 전";
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}일 전`;
  const months = Math.floor(days / 30);
  return `${months}개월 전`;
}

interface DiscussionSectionProps {
  stockId: string;
}

export default function DiscussionSection({ stockId }: DiscussionSectionProps) {
  const [discussions, setDiscussions] = useState<DiscussionItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [comments, setComments] = useState<Record<string, CommentItem[]>>({});
  const [commentsLoading, setCommentsLoading] = useState<string | null>(null);
  const [commentsError, setCommentsError] = useState<string | null>(null);
  const [commentInput, setCommentInput] = useState("");
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const loggedIn = isLoggedIn();

  const fetchDiscussions = useCallback(async (p: number, append: boolean = false) => {
    if (!loggedIn) {
      setLoading(false);
      return;
    }
    try {
      const resp = await discussionsApi.list(stockId, p);
      const data = resp.data;
      if (append) {
        setDiscussions((prev) => [...prev, ...data.discussions]);
      } else {
        setDiscussions(data.discussions);
      }
      setHasMore(data.pagination.has_more);
      setTotal(data.pagination.total);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [stockId, loggedIn]);

  useEffect(() => {
    fetchDiscussions(1);
  }, [fetchDiscussions]);

  const handleSubmit = async () => {
    if (!content.trim() || submitting) return;
    setSubmitting(true);
    try {
      const resp = await discussionsApi.create(stockId, content.trim());
      setDiscussions((prev) => [resp.data, ...prev]);
      setTotal((prev) => prev + 1);
      setContent("");
    } catch {
      // handled by api interceptor
    } finally {
      setSubmitting(false);
    }
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    setLoadingMore(true);
    fetchDiscussions(nextPage, true);
  };

  const handleEditStart = (d: DiscussionItem) => {
    setEditingId(d.id);
    setEditContent(d.content);
    setMenuOpenId(null);
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditContent("");
  };

  const handleEditSave = async (discussionId: string) => {
    if (!editContent.trim()) return;
    try {
      const resp = await discussionsApi.update(discussionId, editContent.trim());
      setDiscussions((prev) =>
        prev.map((d) => (d.id === discussionId ? resp.data : d))
      );
      setEditingId(null);
      setEditContent("");
      addToast("수정되었습니다", "success");
    } catch {
      addToast("처리에 실패했습니다", "error");
    }
  };

  const handleDeleteConfirm = async (discussionId: string) => {
    try {
      await discussionsApi.delete(discussionId);
      setDiscussions((prev) => prev.filter((d) => d.id !== discussionId));
      setTotal((prev) => prev - 1);
      setDeleteConfirmId(null);
      if (expandedId === discussionId) setExpandedId(null);
      addToast("삭제되었습니다", "success");
    } catch {
      addToast("처리에 실패했습니다", "error");
    }
  };

  const handleEditKeyDown = (e: React.KeyboardEvent, discussionId: string) => {
    if (e.key === "Escape") {
      handleEditCancel();
    }
  };

  const handleToggleExpand = async (discussionId: string) => {
    if (expandedId === discussionId) {
      setExpandedId(null);
      setCommentInput("");
      return;
    }
    setExpandedId(discussionId);
    setCommentInput("");
    setCommentsError(null);
    if (!comments[discussionId]) {
      setCommentsLoading(discussionId);
      try {
        const resp = await discussionsApi.listComments(discussionId);
        setComments((prev) => ({ ...prev, [discussionId]: resp.data }));
      } catch {
        setCommentsError(discussionId);
      } finally {
        setCommentsLoading(null);
      }
    }
  };

  const handleCommentSubmit = async (discussionId: string) => {
    if (!commentInput.trim() || commentSubmitting) return;
    setCommentSubmitting(true);
    try {
      const resp = await discussionsApi.createComment(discussionId, commentInput.trim());
      setComments((prev) => ({
        ...prev,
        [discussionId]: [...(prev[discussionId] || []), resp.data],
      }));
      setDiscussions((prev) =>
        prev.map((d) =>
          d.id === discussionId ? { ...d, comment_count: d.comment_count + 1 } : d
        )
      );
      setCommentInput("");
    } catch {
      addToast("처리에 실패했습니다", "error");
    } finally {
      setCommentSubmitting(false);
    }
  };

  const handleCommentDelete = async (discussionId: string, commentId: string) => {
    try {
      await discussionsApi.deleteComment(commentId);
      setComments((prev) => ({
        ...prev,
        [discussionId]: (prev[discussionId] || []).filter((c) => c.id !== commentId),
      }));
      setDiscussions((prev) =>
        prev.map((d) =>
          d.id === discussionId ? { ...d, comment_count: Math.max(0, d.comment_count - 1) } : d
        )
      );
      addToast("삭제되었습니다", "success");
    } catch {
      addToast("처리에 실패했습니다", "error");
    }
  };

  return (
    <div className="mt-6" data-testid="discussion-section">
      <h3 className="text-lg font-bold text-gray-900 mb-4" data-testid="discussion-title">
        💬 토론
      </h3>

      {/* Write form */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4 relative" data-testid="discussion-form">
        <textarea
          className="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
          placeholder="이 종목에 대한 의견을 남겨보세요"
          maxLength={2000}
          rows={3}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          disabled={!loggedIn}
          data-testid="discussion-textarea"
        />
        {!loggedIn && (
          <div
            className="absolute inset-0 bg-white/80 flex items-center justify-center rounded-lg"
            data-testid="discussion-login-overlay"
          >
            <p className="text-sm text-gray-500">
              로그인 후 작성할 수 있습니다{" "}
              <a href="/login" className="text-blue-600 hover:underline" data-testid="discussion-login-link">
                로그인
              </a>
            </p>
          </div>
        )}
        {loggedIn && (
          <div className="flex justify-between items-center mt-2">
            <span className="text-xs text-gray-400">{content.length}/2000</span>
            <button
              onClick={handleSubmit}
              disabled={!content.trim() || submitting}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="discussion-submit-btn"
            >
              {submitting ? "게시 중..." : "게시"}
            </button>
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      {deleteConfirmId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" data-testid="discussion-delete-dialog">
          <div className="bg-white rounded-lg p-6 max-w-sm mx-4" role="dialog">
            <p className="text-sm text-gray-900 mb-1 font-semibold">글을 삭제하시겠습니까?</p>
            <p className="text-sm text-gray-500 mb-4" data-testid="discussion-delete-warning">
              삭제하면 댓글도 함께 삭제됩니다
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                data-testid="discussion-delete-cancel"
              >
                취소
              </button>
              <button
                onClick={() => handleDeleteConfirm(deleteConfirmId)}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"
                data-testid="discussion-delete-confirm"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Discussion list */}
      {loading ? (
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
        </div>
      ) : discussions.length === 0 ? (
        <div
          className="bg-white rounded-lg border border-gray-200 py-12 text-center"
          data-testid="empty-discussions"
        >
          <p className="text-gray-400 text-sm">
            아직 토론이 없습니다. 첫 번째 글을 작성해보세요!
          </p>
        </div>
      ) : (
        <div className="space-y-3" data-testid="discussion-list">
          {discussions.map((d) => (
            <div
              key={d.id}
              className="bg-white rounded-lg border border-gray-200 p-4"
              data-testid="discussion-item"
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-gray-900" data-testid="discussion-author">
                    {d.author_name}
                  </span>
                  <span className="text-xs text-gray-400" data-testid="discussion-time">
                    {formatRelativeTime(d.created_at)}
                  </span>
                </div>
                {d.is_mine && editingId !== d.id && (
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuOpenId(menuOpenId === d.id ? null : d.id);
                      }}
                      className="text-gray-400 hover:text-gray-600 px-1"
                      data-testid="discussion-more-btn"
                      aria-label="토론 관리 메뉴"
                    >
                      ⋯
                    </button>
                    {menuOpenId === d.id && (
                      <div
                        className="absolute right-0 top-6 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-10 min-w-[100px]"
                        data-testid="discussion-more-menu"
                      >
                        <button
                          onClick={() => handleEditStart(d)}
                          className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                          data-testid="discussion-edit-btn"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => {
                            setDeleteConfirmId(d.id);
                            setMenuOpenId(null);
                          }}
                          className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-50"
                          data-testid="discussion-delete-btn"
                        >
                          삭제
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {editingId === d.id ? (
                <div data-testid="discussion-edit-form">
                  <textarea
                    className="w-full border border-gray-300 rounded-lg p-3 text-sm text-gray-900 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    maxLength={2000}
                    rows={3}
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    onKeyDown={(e) => handleEditKeyDown(e, d.id)}
                    data-testid="discussion-edit-textarea"
                    autoFocus
                  />
                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      onClick={handleEditCancel}
                      className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800"
                      data-testid="discussion-edit-cancel"
                    >
                      취소
                    </button>
                    <button
                      onClick={() => handleEditSave(d.id)}
                      disabled={!editContent.trim()}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      data-testid="discussion-edit-save"
                    >
                      저장
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Clickable area for expand/collapse (accordion) */}
                  <div
                    className="cursor-pointer min-h-[48px]"
                    onClick={() => handleToggleExpand(d.id)}
                    data-testid="discussion-toggle"
                  >
                    {expandedId === d.id ? (
                      <p className="text-sm text-gray-700" data-testid="discussion-full-content">
                        {d.content}
                      </p>
                    ) : (
                      <p
                        className="text-sm text-gray-700 line-clamp-2"
                        data-testid="discussion-content"
                      >
                        {d.content}
                      </p>
                    )}
                  </div>
                  <div className="mt-2">
                    <span className="text-xs text-gray-400" data-testid="discussion-comment-count">
                      💬 {d.comment_count}
                    </span>
                  </div>

                  {/* Expanded comments section (inline accordion) */}
                  {expandedId === d.id && (
                    <div className="mt-3 pt-3 border-t border-gray-100" data-testid="discussion-comments-section">
                      {commentsLoading === d.id ? (
                        <div className="flex justify-center py-4">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
                        </div>
                      ) : commentsError === d.id ? (
                        <p className="text-sm text-red-500 py-2" data-testid="comments-error">
                          댓글을 불러올 수 없습니다
                        </p>
                      ) : (comments[d.id] || []).length === 0 ? (
                        <p className="text-sm text-gray-400 py-2" data-testid="empty-comments">
                          아직 댓글이 없습니다
                        </p>
                      ) : (
                        <div className="space-y-2" data-testid="comment-list">
                          {(comments[d.id] || []).map((c) => (
                            <div key={c.id} className="flex items-start gap-2" data-testid="comment-item">
                              <div className="flex-1 min-w-0">
                                <span className="font-bold text-gray-900" style={{ fontSize: "12px" }} data-testid="comment-author">
                                  {c.author_name}
                                </span>
                                <p className="text-gray-700" style={{ fontSize: "14px" }} data-testid="comment-content">
                                  {c.content}
                                </p>
                                <span className="text-gray-400" style={{ fontSize: "12px" }} data-testid="comment-time">
                                  {formatRelativeTime(c.created_at)}
                                </span>
                              </div>
                              {c.is_mine && (
                                <button
                                  onClick={() => handleCommentDelete(d.id, c.id)}
                                  className="text-xs text-red-500 hover:text-red-700 shrink-0"
                                  data-testid="comment-delete-btn"
                                >
                                  삭제
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Comment input */}
                      <div className="mt-3 relative" data-testid="comment-form">
                        <div className="flex gap-2">
                          <input
                            type="text"
                            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                            placeholder="댓글을 입력하세요"
                            maxLength={500}
                            value={commentInput}
                            onChange={(e) => setCommentInput(e.target.value)}
                            disabled={!loggedIn}
                            data-testid="comment-input"
                          />
                          <button
                            onClick={() => handleCommentSubmit(d.id)}
                            disabled={!commentInput.trim() || commentSubmitting || !loggedIn}
                            className="px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                            data-testid="comment-submit-btn"
                          >
                            등록
                          </button>
                        </div>
                        {!loggedIn && (
                          <p className="text-xs text-gray-400 mt-1" data-testid="comment-login-notice">
                            로그인이 필요합니다
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}

          {hasMore && (
            <button
              onClick={handleLoadMore}
              disabled={loadingMore}
              className="w-full py-3 text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
              data-testid="discussion-load-more"
            >
              {loadingMore ? "불러오는 중..." : "이전 글 더 보기"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
