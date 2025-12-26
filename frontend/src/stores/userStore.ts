// stores/userStore.ts
import { defineStore } from 'pinia'

// 定义场景类型
export type SceneType = 'it' | 'language' | 'cert'

export const useUserStore = defineStore('user', {
  state: () => ({
    userId: localStorage.getItem('userId') || '1',
    currentKbId: null as number | null,
    sceneType: 'it' as SceneType
  }),
  getters: {
    kbId: (state) => state.currentKbId
  },
  actions: {
    setKbId(kbId: number) {
      this.currentKbId = kbId
    },
    setScene(scene: SceneType) {
      this.sceneType = scene
    },
    saveUserId() {
      localStorage.setItem('userId', this.userId)
    }
  }
})
