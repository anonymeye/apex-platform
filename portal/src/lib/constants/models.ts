// Open Source LLM Models
export interface LLMModel {
  id: string
  name: string
  provider: string
  description: string
  size?: string
}

export const OPEN_SOURCE_MODELS: LLMModel[] = [
  // LLaMA Models
  {
    id: "llama-3-8b",
    name: "LLaMA 3 8B",
    provider: "Meta",
    description: "8 billion parameter model, good balance of performance and speed",
    size: "8B",
  },
  {
    id: "llama-3-70b",
    name: "LLaMA 3 70B",
    provider: "Meta",
    description: "70 billion parameter model, high performance",
    size: "70B",
  },
  {
    id: "llama-2-7b",
    name: "LLaMA 2 7B",
    provider: "Meta",
    description: "7 billion parameter model, efficient and fast",
    size: "7B",
  },
  {
    id: "llama-2-13b",
    name: "LLaMA 2 13B",
    provider: "Meta",
    description: "13 billion parameter model, improved performance",
    size: "13B",
  },
  {
    id: "llama-2-70b",
    name: "LLaMA 2 70B",
    provider: "Meta",
    description: "70 billion parameter model, best performance",
    size: "70B",
  },
  
  // Mistral Models
  {
    id: "mistral-7b",
    name: "Mistral 7B",
    provider: "Mistral AI",
    description: "7B parameter model, strong instruction following",
    size: "7B",
  },
  {
    id: "mistral-8x7b",
    name: "Mixtral 8x7B",
    provider: "Mistral AI",
    description: "Mixture of experts, 8x7B parameters",
    size: "47B",
  },
  {
    id: "mistral-large",
    name: "Mistral Large",
    provider: "Mistral AI",
    description: "Large model with excellent reasoning",
    size: "Large",
  },
  
  // Qwen Models
  {
    id: "qwen-7b",
    name: "Qwen 7B",
    provider: "Alibaba",
    description: "7B parameter model, multilingual support",
    size: "7B",
  },
  {
    id: "qwen-14b",
    name: "Qwen 14B",
    provider: "Alibaba",
    description: "14B parameter model, enhanced capabilities",
    size: "14B",
  },
  {
    id: "qwen-72b",
    name: "Qwen 72B",
    provider: "Alibaba",
    description: "72B parameter model, high performance",
    size: "72B",
  },
  
  // Phi Models
  {
    id: "phi-2",
    name: "Phi-2",
    provider: "Microsoft",
    description: "2.7B parameter model, small but capable",
    size: "2.7B",
  },
  {
    id: "phi-3-mini",
    name: "Phi-3 Mini",
    provider: "Microsoft",
    description: "3.8B parameter model, efficient",
    size: "3.8B",
  },
  {
    id: "phi-3-medium",
    name: "Phi-3 Medium",
    provider: "Microsoft",
    description: "14B parameter model, balanced performance",
    size: "14B",
  },
  
  // Gemma Models
  {
    id: "gemma-2b",
    name: "Gemma 2B",
    provider: "Google",
    description: "2B parameter model, lightweight",
    size: "2B",
  },
  {
    id: "gemma-7b",
    name: "Gemma 7B",
    provider: "Google",
    description: "7B parameter model, good performance",
    size: "7B",
  },
  
  // Other Models
  {
    id: "falcon-7b",
    name: "Falcon 7B",
    provider: "TII",
    description: "7B parameter model from Technology Innovation Institute",
    size: "7B",
  },
  {
    id: "falcon-40b",
    name: "Falcon 40B",
    provider: "TII",
    description: "40B parameter model, high performance",
    size: "40B",
  },
  {
    id: "neural-chat-7b",
    name: "Neural Chat 7B",
    provider: "Intel",
    description: "7B parameter model optimized for chat",
    size: "7B",
  },
]

export function getModelById(id: string): LLMModel | undefined {
  return OPEN_SOURCE_MODELS.find((model) => model.id === id)
}

export function searchModels(query: string): LLMModel[] {
  const queryLower = query.toLowerCase()
  return OPEN_SOURCE_MODELS.filter(
    (model) =>
      model.name.toLowerCase().includes(queryLower) ||
      model.provider.toLowerCase().includes(queryLower) ||
      model.description.toLowerCase().includes(queryLower) ||
      model.id.toLowerCase().includes(queryLower)
  )
}

// Helper to find model_id from backend model_provider and model_name
// Backend stores provider as lowercase with dashes (e.g., "meta", "mistral-ai")
export function getModelIdFromBackendData(
  model_provider: string,
  model_name: string
): string | undefined {
  // Normalize provider: convert to lowercase and replace spaces with dashes
  const normalizedProvider = model_provider.toLowerCase().replace(/\s+/g, "-")
  
  // Find matching model by comparing normalized provider and exact model name
  const model = OPEN_SOURCE_MODELS.find((m) => {
    const modelProviderNormalized = m.provider.toLowerCase().replace(/\s+/g, "-")
    return modelProviderNormalized === normalizedProvider && m.name === model_name
  })
  
  return model?.id
}
