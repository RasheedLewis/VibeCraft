/**
 * Helper function to determine if animations should be disabled.
 * Animations are disabled if:
 * - The view is public (isPublicView is true), OR
 * - The user has disabled animations in their preferences
 */
export function shouldDisableAnimations(
  isPublicView: boolean,
  userAnimationsDisabled?: boolean,
): boolean {
  return isPublicView || userAnimationsDisabled === true
}
