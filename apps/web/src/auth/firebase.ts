import type { AuthAdapter } from './auth'

/** Public web config of the env's Firebase project (not secrets; set at build time). */
export interface FirebaseWebConfig {
  apiKey: string
  authDomain: string
  projectId: string
  appId: string
}

export function firebaseConfigFromEnv(
  env: Record<string, string | undefined>,
): FirebaseWebConfig | null {
  const c = {
    apiKey: env.VITE_FIREBASE_API_KEY ?? '',
    authDomain: env.VITE_FIREBASE_AUTH_DOMAIN ?? '',
    projectId: env.VITE_FIREBASE_PROJECT_ID ?? '',
    appId: env.VITE_FIREBASE_APP_ID ?? '',
  }
  return Object.values(c).every((v) => v.length > 0) ? c : null
}

/** Google sign-in through Firebase Auth. The SDK loads on first use, so demo mode never ships it. */
export function firebaseAuth(config: FirebaseWebConfig): AuthAdapter {
  const sdk = (async () => {
    const [{ initializeApp }, auth] = await Promise.all([
      import('firebase/app'),
      import('firebase/auth'),
    ])
    return { auth, instance: auth.getAuth(initializeApp(config)) }
  })()
  return {
    subscribe(cb) {
      let unsubscribe = () => {}
      let stopped = false
      void sdk.then(({ auth, instance }) => {
        if (stopped) return
        unsubscribe = auth.onAuthStateChanged(instance, (u) => cb(u?.email ?? null))
      })
      return () => {
        stopped = true
        unsubscribe()
      }
    },
    async signIn() {
      const { auth, instance } = await sdk
      await auth.signInWithPopup(instance, new auth.GoogleAuthProvider())
    },
    async signOut() {
      const { auth, instance } = await sdk
      await auth.signOut(instance)
    },
    async token() {
      const { instance } = await sdk
      return instance.currentUser ? instance.currentUser.getIdToken() : null
    },
  }
}
