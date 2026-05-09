import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface SimulatorState {
  scenario: string
  currentStep: number
  totalSteps: number
  isPlaying: boolean
  speed: number
  packets: PacketInfo[]
}

export interface PacketInfo {
  id: string
  from: 'client' | 'server'
  to: 'client' | 'server'
  seq: number
  ack: number
  flags: string[]
  data: string
}

export const useSimulatorStore = defineStore('simulator', () => {
  const scenario = ref<string>('three_way_handshake')
  const isPlaying = ref<boolean>(false)
  const currentStep = ref<number>(0)
  const speed = ref<number>(1)
  const packets = ref<PacketInfo[]>([])

  function setScenario(name: string) {
    scenario.value = name
    currentStep.value = 0
    isPlaying.value = false
    packets.value = []
  }

  function play() {
    isPlaying.value = true
  }

  function pause() {
    isPlaying.value = false
  }

  function reset() {
    currentStep.value = 0
    isPlaying.value = false
  }

  return {
    scenario,
    isPlaying,
    currentStep,
    speed,
    packets,
    setScenario,
    play,
    pause,
    reset,
  }
})
