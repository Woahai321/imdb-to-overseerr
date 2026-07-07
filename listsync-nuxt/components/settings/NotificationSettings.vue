<template>
  <Card class="glass-card border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300">
    <div class="space-y-4">
      <!-- Header -->
      <div class="flex items-center gap-2.5">
        <div class="p-2 rounded-lg bg-gradient-to-br from-purple-600/20 to-purple-500/10 border border-purple-500/30">
          <BellIcon class="w-4 h-4 text-purple-400" />
        </div>
        <div>
          <h3 class="text-base font-bold titillium-web-semibold">
            Notification Settings
          </h3>
          <p class="text-[10px] text-muted-foreground font-medium">
            Configure notification preferences
          </p>
        </div>
      </div>

      <!-- Discord Section -->
      <div class="space-y-4 p-3 rounded-lg bg-purple-500/5 border border-purple-500/10">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-purple-300 uppercase tracking-wide">Discord</span>
          <Button
            variant="secondary"
            size="sm"
            @click="$emit('test-notification')"
          >
            <SendIcon class="w-4 h-4 mr-2" />
            Send Test
          </Button>
        </div>

        <!-- Discord Webhook -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Discord Webhook URL
          </label>
          <Input
            v-model="localValue.discordWebhook"
            type="url"
            placeholder="https://discord.com/api/webhooks/..."
            :icon="MessageSquareIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1.5">
            Get notified in Discord when sync completes
          </p>
        </div>

        <!-- Discord Notifications Toggle -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Discord Notifications
          </label>
          <div class="flex items-center gap-3">
            <!-- Status Label -->
            <span
              :class="[
                'text-sm font-semibold tabular-nums',
                localValue.enabled ? 'text-green-400' : 'text-gray-400'
              ]"
            >
              {{ localValue.enabled ? 'ON' : 'OFF' }}
            </span>

            <!-- Toggle Switch -->
            <button
              type="button"
              role="switch"
              :aria-checked="localValue.enabled"
              :class="[
                'relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-black',
                localValue.enabled ? 'bg-green-500' : 'bg-gray-600'
              ]"
              @click="toggleEnabled"
            >
              <span
                :class="[
                  'inline-flex items-center justify-center h-6 w-6 transform rounded-full bg-white shadow-lg transition-all duration-200',
                  localValue.enabled ? 'translate-x-7' : 'translate-x-0.5'
                ]"
              >
                <!-- Icon inside toggle -->
                <CheckIcon v-if="localValue.enabled" :size="14" class="text-green-500" />
                <XIcon v-else :size="14" class="text-gray-600" />
              </span>
            </button>

            <span class="text-sm text-muted-foreground">
              {{ localValue.enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <p class="text-xs text-muted-foreground mt-1.5">
            Send sync completion summary to Discord
          </p>
        </div>
      </div>

      <!-- Telegram Section -->
      <div class="space-y-4 p-3 rounded-lg bg-purple-500/5 border border-purple-500/10">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-purple-300 uppercase tracking-wide">Telegram</span>
          <Button
            variant="secondary"
            size="sm"
            @click="$emit('test-telegram')"
          >
            <SendIcon class="w-4 h-4 mr-2" />
            Send Test
          </Button>
        </div>

        <!-- Telegram Bot Token -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Telegram Bot Token
          </label>
          <Input
            v-model="localValue.telegramBotToken"
            type="password"
            placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
            :icon="KeyIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1.5">
            Create a bot with @BotFather to get your token
          </p>
        </div>

        <!-- Telegram Chat ID -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Telegram Chat ID
          </label>
          <Input
            v-model="localValue.telegramChatId"
            type="text"
            placeholder="-1001234567890"
            :icon="MessageSquareIcon"
            @update:model-value="emitUpdate"
          />
          <p class="text-xs text-muted-foreground mt-1.5">
            User, group or channel ID that receives the notifications
          </p>
        </div>

        <!-- Telegram Notifications Toggle -->
        <div>
          <label class="block text-xs font-semibold mb-2 text-foreground">
            Telegram Notifications
          </label>
          <div class="flex items-center gap-3">
            <!-- Status Label -->
            <span
              :class="[
                'text-sm font-semibold tabular-nums',
                localValue.telegramEnabled ? 'text-green-400' : 'text-gray-400'
              ]"
            >
              {{ localValue.telegramEnabled ? 'ON' : 'OFF' }}
            </span>

            <!-- Toggle Switch -->
            <button
              type="button"
              role="switch"
              :aria-checked="localValue.telegramEnabled"
              :class="[
                'relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-black',
                localValue.telegramEnabled ? 'bg-green-500' : 'bg-gray-600'
              ]"
              @click="toggleTelegramEnabled"
            >
              <span
                :class="[
                  'inline-flex items-center justify-center h-6 w-6 transform rounded-full bg-white shadow-lg transition-all duration-200',
                  localValue.telegramEnabled ? 'translate-x-7' : 'translate-x-0.5'
                ]"
              >
                <!-- Icon inside toggle -->
                <CheckIcon v-if="localValue.telegramEnabled" :size="14" class="text-green-500" />
                <XIcon v-else :size="14" class="text-gray-600" />
              </span>
            </button>

            <span class="text-sm text-muted-foreground">
              {{ localValue.telegramEnabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <p class="text-xs text-muted-foreground mt-1.5">
            Send sync completion summary to Telegram
          </p>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup lang="ts">
import {
  Bell as BellIcon,
  Send as SendIcon,
  MessageSquare as MessageSquareIcon,
  Key as KeyIcon,
  Check as CheckIcon,
  X as XIcon,
} from 'lucide-vue-next'

interface NotificationSettings {
  discordWebhook: string
  enabled: boolean
  telegramBotToken: string
  telegramChatId: string
  telegramEnabled: boolean
}

interface Props {
  modelValue: NotificationSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: NotificationSettings]
  'test-notification': []
  'test-telegram': []
}>()

const localValue = ref({ ...props.modelValue })

// Watch for external changes
watch(
  () => props.modelValue,
  (newValue) => {
    localValue.value = { ...newValue }
  },
  { deep: true }
)

// Emit updates
const emitUpdate = () => {
  emit('update:modelValue', { ...localValue.value })
}

// Toggle functions
const toggleEnabled = () => {
  localValue.value.enabled = !localValue.value.enabled
  emitUpdate()
}

const toggleTelegramEnabled = () => {
  localValue.value.telegramEnabled = !localValue.value.telegramEnabled
  emitUpdate()
}
</script>
