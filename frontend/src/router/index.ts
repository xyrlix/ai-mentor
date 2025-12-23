import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('../views/UploadView.vue')
    },
    {
      path: '/interview',
      name: 'interview',
      component: () => import('../views/InterviewView.vue')
    },
    {
      path: '/report',
      name: 'report',
      component: () => import('../views/ReportView.vue')
    },
    {
      path: '/qna',
      name: 'qna',
      component: () => import('../views/QnAView.vue')
    },
    {
      path: '/exam',
      name: 'exam',
      component: () => import('../views/ExamView.vue')
    }
  ]
})

export default router
