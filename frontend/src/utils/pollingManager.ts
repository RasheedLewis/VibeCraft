/**
 * Global polling manager that runs outside of React.
 * Uses a single setTimeout loop that's set once on app load.
 * DRASTIC: Global mutex ensures only ONE HTTP request can execute at a time, globally.
 * Components register URLs and handlers - the manager makes the actual HTTP requests.
 */

import { apiClient } from '../lib/apiClient'

type PollResponseHandler<T = unknown> = (data: T) => void | Promise<void>

interface PollSubscription {
  id: string
  url: string
  handler: PollResponseHandler
  interval: number
  lastPolled: number
}

class PollingManager {
  private static instance: PollingManager | null = null
  private subscription: PollSubscription | null = null // ONLY ONE subscription allowed
  private timeoutId: number | undefined = undefined
  private isRunning = false
  private minPollInterval = 5000 // Minimum 5 seconds between polls

  // GLOBAL MUTEX: Only ONE HTTP request can execute at a time, globally
  private isPolling = false
  private currentPollAbortController: AbortController | null = null

  private constructor() {
    // Private constructor for singleton
  }

  static getInstance(): PollingManager {
    if (!PollingManager.instance) {
      PollingManager.instance = new PollingManager()
    }
    return PollingManager.instance
  }

  /**
   * Start the global polling loop (called once on app load)
   */
  start(): void {
    if (this.isRunning) {
      return
    }
    console.log('[PollingManager] Starting global polling loop')
    this.isRunning = true
    this.scheduleNextPoll()
  }

  /**
   * Stop the global polling loop
   */
  stop(): void {
    this.isRunning = false
    if (this.timeoutId !== undefined) {
      window.clearTimeout(this.timeoutId)
      this.timeoutId = undefined
    }
    // Cancel any in-flight poll
    if (this.currentPollAbortController) {
      this.currentPollAbortController.abort()
      this.currentPollAbortController = null
    }
    this.isPolling = false
  }

  /**
   * Register a URL to be polled
   * DRASTIC: Only ONE subscription allowed globally - replaces any existing subscription
   * @param id Unique identifier for this subscription
   * @param url The URL to poll
   * @param handler Function to call with the response data
   * @param interval Optional custom interval (defaults to minPollInterval)
   */
  subscribe(
    id: string,
    url: string,
    handler: PollResponseHandler,
    interval?: number,
  ): void {
    // DRASTIC MEASURE: Only allow ONE subscription globally
    // If a new subscription is created, it REPLACES the old one
    if (this.subscription && this.subscription.id !== id) {
      console.log(
        `[PollingManager] Replacing subscription ${this.subscription.id} with ${id}`,
      )
      // Cancel any in-flight poll from the old subscription
      if (this.currentPollAbortController) {
        this.currentPollAbortController.abort()
        this.currentPollAbortController = null
      }
      this.isPolling = false
    }

    this.subscription = {
      id,
      url,
      handler,
      interval: Math.max(interval ?? this.minPollInterval, this.minPollInterval), // Enforce minimum
      lastPolled: 0,
    }

    console.log(
      `[PollingManager] Subscribed: ${id} -> ${url} (interval: ${this.subscription.interval}ms)`,
    )

    // Start polling if not already running
    if (!this.isRunning) {
      this.start()
    }
  }

  /**
   * Unregister a subscription
   */
  unsubscribe(id: string): void {
    if (this.subscription && this.subscription.id === id) {
      // Cancel any in-flight poll
      if (this.currentPollAbortController) {
        this.currentPollAbortController.abort()
        this.currentPollAbortController = null
      }
      this.isPolling = false
      this.subscription = null
      // Stop polling if no subscription left
      this.stop()
    }
  }

  /**
   * Check if a subscription exists
   */
  hasSubscription(id: string): boolean {
    return this.subscription?.id === id
  }

  /**
   * Check if a poll is currently executing (global mutex check)
   */
  isCurrentlyPolling(): boolean {
    return this.isPolling
  }

  private scheduleNextPoll(): void {
    if (!this.isRunning) {
      return
    }

    // If no subscription, stop polling
    if (!this.subscription) {
      this.stop()
      return
    }

    // GLOBAL MUTEX: If a poll is already executing, wait and reschedule
    // This ensures only ONE HTTP request happens at a time, globally
    if (this.isPolling) {
      // Poll is in progress, check again in 100ms
      // The current poll will complete and release the mutex, then we'll retry
      this.timeoutId = window.setTimeout(() => {
        this.scheduleNextPoll()
      }, 100)
      return
    }

    const now = Date.now()
    const timeSinceLastPoll = now - this.subscription.lastPolled
    const timeUntilReady = this.subscription.interval - timeSinceLastPoll

    if (timeSinceLastPoll >= this.subscription.interval) {
      // Subscription is ready to poll - execute it
      console.log(
        `[PollingManager] Executing poll for ${this.subscription.id} -> ${this.subscription.url}`,
      )
      this.executePoll(this.subscription)
      // Schedule next poll after minimum interval
      this.timeoutId = window.setTimeout(() => {
        this.scheduleNextPoll()
      }, this.minPollInterval)
    } else {
      // Schedule next poll for when subscription will be ready
      const delay = Math.max(100, timeUntilReady)
      this.timeoutId = window.setTimeout(() => {
        this.scheduleNextPoll()
      }, delay)
    }
  }

  private async executePoll(subscription: PollSubscription): Promise<void> {
    // GLOBAL MUTEX: Only one poll can execute at a time
    if (this.isPolling) {
      console.log('[PollingManager] Poll already in progress, skipping')
      return
    }

    // Acquire the mutex
    this.isPolling = true
    this.currentPollAbortController = new AbortController()
    const abortSignal = this.currentPollAbortController.signal

    try {
      // Check if subscription was replaced (abort signal was triggered)
      if (abortSignal.aborted) {
        console.log(`[PollingManager] Poll aborted for subscription ${subscription.id}`)
        return
      }

      // Check if page is visible (pause polling when tab is hidden)
      if (document.hidden) {
        // Skip this poll, will retry next cycle
        // Don't update lastPolled so it will retry immediately when page becomes visible
        return
      }

      // Update lastPolled only if we're actually going to poll
      subscription.lastPolled = Date.now()

      // Make the HTTP request directly (the manager controls the request)
      // apiClient already has baseURL set, so use the URL as-is
      const response = await Promise.race([
        apiClient.get(subscription.url),
        new Promise<never>((_, reject) => {
          abortSignal.addEventListener('abort', () => {
            reject(new Error('Poll aborted - subscription replaced'))
          })
        }),
      ])

      // Check again if subscription was replaced during the request
      if (abortSignal.aborted) {
        console.log(
          `[PollingManager] Poll aborted during request for subscription ${subscription.id}`,
        )
        return
      }

      // Call the handler with the response data
      try {
        await subscription.handler(response.data)
      } catch (handlerError) {
        console.error(
          `[PollingManager] Error in handler for subscription ${subscription.id}:`,
          handlerError,
        )
        // Don't rethrow - we'll retry on next cycle
      }
    } catch (error) {
      if (
        error instanceof Error &&
        error.message === 'Poll aborted - subscription replaced'
      ) {
        console.log(`[PollingManager] Poll aborted for subscription ${subscription.id}`)
      } else {
        console.error(`[PollingManager] Error polling ${subscription.url}:`, error)
        // On error, the handler won't be called, but we'll retry on next cycle
      }
    } finally {
      // Release the mutex
      this.isPolling = false
      // Clear abort controller if it's still the one we created (wasn't replaced)
      if (
        this.currentPollAbortController &&
        this.currentPollAbortController.signal === abortSignal
      ) {
        this.currentPollAbortController = null
      }
    }
  }
}

// Export singleton instance
export const pollingManager = PollingManager.getInstance()

// Auto-start on module load (only happens once)
if (typeof window !== 'undefined') {
  // Start polling manager when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      pollingManager.start()
    })
  } else {
    pollingManager.start()
  }
}
