/**
 * Offline Storage for LAWTRIX PWA
 *
 * Stores drafts locally when offline using IndexedDB.
 * Drafts are synced to the server when connectivity returns.
 */

import { get, set, del, keys, clear } from 'idb-keyval'

export type DraftType = 'rti' | 'cpgrams' | 'scheme' | 'consumer' | 'tenant' | 'labour'
export type SyncStatus = 'pending' | 'syncing' | 'synced' | 'failed'

export interface OfflineDraft {
  id: string
  type: DraftType
  data: Record<string, any>
  createdAt: string
  updatedAt: string
  syncStatus: SyncStatus
  syncAttempts: number
  lastSyncError?: string
}

export class OfflineStore {
  private keyPrefix = 'lawtrix_draft_'

  /**
   * Save a draft to offline storage
   */
  async saveDraft(type: DraftType, data: Record<string, any>, id?: string): Promise<string> {
    const draftId = id || `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const key = this.keyPrefix + draftId

    const draft: OfflineDraft = {
      id: draftId,
      type,
      data,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      syncStatus: 'pending',
      syncAttempts: 0,
    }

    await set(key, draft)
    return draftId
  }

  /**
   * Get a specific draft by ID
   */
  async getDraft(id: string): Promise<OfflineDraft | null> {
    const key = this.keyPrefix + id
    const draft = await get<OfflineDraft>(key)
    return draft || null
  }

  /**
   * Get all drafts, optionally filtered by type
   */
  async getDrafts(type?: DraftType): Promise<OfflineDraft[]> {
    const allKeys = await keys()
    const draftKeys = allKeys.filter(k =>
      typeof k === 'string' && k.startsWith(this.keyPrefix)
    ) as string[]

    const drafts = await Promise.all(
      draftKeys.map(async (key) => {
        const draft = await get<OfflineDraft>(key)
        return draft
      })
    )

    const validDrafts = drafts.filter((d): d is OfflineDraft => d !== null && d !== undefined)

    if (type) {
      return validDrafts.filter(d => d.type === type)
    }

    return validDrafts
  }

  /**
   * Get drafts by sync status
   */
  async getDraftsByStatus(status: SyncStatus): Promise<OfflineDraft[]> {
    const allDrafts = await this.getDrafts()
    return allDrafts.filter(d => d.syncStatus === status)
  }

  /**
   * Update draft sync status
   */
  async updateDraftStatus(
    id: string,
    status: SyncStatus,
    error?: string
  ): Promise<void> {
    const draft = await this.getDraft(id)
    if (!draft) {
      throw new Error(`Draft ${id} not found`)
    }

    draft.syncStatus = status
    draft.updatedAt = new Date().toISOString()

    if (status === 'failed') {
      draft.syncAttempts += 1
      draft.lastSyncError = error
    } else if (status === 'synced') {
      draft.lastSyncError = undefined
    }

    const key = this.keyPrefix + id
    await set(key, draft)
  }

  /**
   * Delete a draft
   */
  async deleteDraft(id: string): Promise<void> {
    const key = this.keyPrefix + id
    await del(key)
  }

  /**
   * Delete all synced drafts
   */
  async deleteSyncedDrafts(): Promise<void> {
    const syncedDrafts = await this.getDraftsByStatus('synced')
    await Promise.all(
      syncedDrafts.map(draft => this.deleteDraft(draft.id))
    )
  }

  /**
   * Get total draft count
   */
  async getDraftCount(): Promise<number> {
    const drafts = await this.getDrafts()
    return drafts.length
  }

  /**
   * Get pending draft count
   */
  async getPendingCount(): Promise<number> {
    const pending = await this.getDraftsByStatus('pending')
    return pending.length
  }

  /**
   * Clear all drafts (use with caution)
   */
  async clearAll(): Promise<void> {
    const allKeys = await keys()
    const draftKeys = allKeys.filter(k =>
      typeof k === 'string' && k.startsWith(this.keyPrefix)
    )
    await Promise.all(draftKeys.map(key => del(key)))
  }
}

// Singleton instance
let storeInstance: OfflineStore | null = null

export function getOfflineStore(): OfflineStore {
  if (!storeInstance) {
    storeInstance = new OfflineStore()
  }
  return storeInstance
}
