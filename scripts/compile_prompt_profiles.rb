#!/usr/bin/env ruby
# frozen_string_literal: true

require 'json'
require 'optparse'
require 'yaml'
require 'fileutils'

ROOT = File.expand_path('..', __dir__)
PROMPTS_DIR = File.join(ROOT, 'prompts')
GENERAL_PATH = File.join(PROMPTS_DIR, 'layers', 'general.yaml')
CHANNELS_DIR = File.join(PROMPTS_DIR, 'channels')
TARGETS_DIR = File.join(PROMPTS_DIR, 'targets')

FIELD_MAP = {
  'youtube-shorts' => {
    format: 'curto',
    selection: 'selection_short_prompt',
    metadata: 'metadata_short_prompt'
  },
  'youtube-long' => {
    format: 'longo',
    selection: 'selection_long_prompt',
    metadata: 'metadata_long_prompt'
  }
}.freeze

def load_yaml(path)
  YAML.safe_load(File.read(path), aliases: false) || {}
rescue Psych::Exception => error
  abort "YAML inválido em #{path}: #{error.message}"
end

def require_text(value, context)
  abort "Campo de texto ausente ou vazio: #{context}" unless value.is_a?(String) && !value.strip.empty?

  value.strip
end

def stage_text(config, stage, context)
  stage_config = config.fetch('stages', {})[stage]
  abort "Etapa #{stage} ausente em #{context}" unless stage_config.is_a?(Hash)

  require_text(stage_config['instructions'], "#{context}.stages.#{stage}.instructions")
end

def prompt_block(title, *instructions)
  ([title] + instructions.map(&:strip)).join("\n\n")
end

options = { channel_id: nil, output_dir: File.join(PROMPTS_DIR, 'compiled') }
OptionParser.new do |parser|
  parser.banner = 'Uso: ruby scripts/compile_prompt_profiles.rb [--channel CHANNEL_ID] [--output-dir DIR]'
  parser.on('--channel CHANNEL_ID', 'Compila apenas o identificador de prompts/channel_id informado') do |value|
    options[:channel_id] = value
  end
  parser.on('--output-dir DIR', 'Diretório de saída dos JSONs compilados') do |value|
    options[:output_dir] = File.expand_path(value)
  end
end.parse!

general = load_yaml(GENERAL_PATH)
channel_paths = Dir.glob(File.join(CHANNELS_DIR, '*.yaml')).sort
channel_paths.select! { |path| File.basename(path, '.yaml') == options[:channel_id] } if options[:channel_id]
abort 'Nenhum arquivo de canal corresponde ao filtro informado.' if channel_paths.empty?

targets = {}
Dir.glob(File.join(TARGETS_DIR, '*.yaml')).sort.each do |path|
  target = load_yaml(path).fetch('target', {})
  target_id = require_text(target['id'], "#{path}.target.id")
  targets[target_id] = load_yaml(path)
end

FileUtils.mkdir_p(options[:output_dir])
compiled_slugs = {}

channel_paths.each do |channel_path|
  channel = load_yaml(channel_path)
  channel_id = require_text(channel['channel_id'], "#{channel_path}.channel_id")
  profile = channel.fetch('profile', {})
  slug = require_text(profile['slug'], "#{channel_path}.profile.slug")
  abort "Slug de perfil duplicado: #{slug}" if compiled_slugs[slug]

  target_ids = channel['targets']
  abort "targets deve ser uma lista não vazia em #{channel_path}" unless target_ids.is_a?(Array) && !target_ids.empty?

  general_selection = stage_text(general, 'selection', GENERAL_PATH)
  general_metadata = stage_text(general, 'metadata', GENERAL_PATH)
  general_thumbnail = stage_text(general, 'thumbnail', GENERAL_PATH)
  channel_selection = stage_text(channel, 'selection', channel_path)
  channel_metadata = stage_text(channel, 'metadata', channel_path)
  channel_thumbnail = stage_text(channel, 'thumbnail', channel_path)

  payload = {
    'slug' => slug,
    'name' => require_text(profile['name'], "#{channel_path}.profile.name"),
    'niche' => require_text(profile['niche'], "#{channel_path}.profile.niche"),
    'niche_aliases' => Array(profile['niche_aliases']).map { |value| require_text(value, "#{channel_path}.profile.niche_aliases[]") },
    'active' => profile.fetch('active', true)
  }

  target_ids.each do |target_id|
    mapping = FIELD_MAP[target_id]
    abort "Alvo não mapeado para as colunas de prompt_profiles: #{target_id}" unless mapping
    target_file = targets[target_id]
    abort "Arquivo YAML ausente para alvo: #{target_id}" unless target_file

    target = target_file.fetch('target', {})
    format = require_text(target['format'], "#{target_id}.target.format")
    abort "Formato inesperado para #{target_id}: #{format}" unless format == mapping[:format]

    payload[mapping[:selection]] = prompt_block(
      'Camada geral',
      general_selection,
      'Camada do canal de destino',
      channel_selection,
      "Camada do alvo #{require_text(target['label'], "#{target_id}.target.label")}",
      stage_text(target_file, 'selection', target_id)
    )
    payload[mapping[:metadata]] = prompt_block(
      'Camada geral',
      general_metadata,
      'Camada do canal de destino',
      channel_metadata,
      "Camada do alvo #{target['label']}",
      stage_text(target_file, 'metadata', target_id)
    )
  end

  abort "Alvo curto ausente para #{channel_id}" unless payload['selection_short_prompt'] && payload['metadata_short_prompt']
  abort "Alvo longo ausente para #{channel_id}" unless payload['selection_long_prompt'] && payload['metadata_long_prompt']

  thumbnail_rules = target_ids.map do |target_id|
    target_file = targets.fetch(target_id)
    target = target_file.fetch('target', {})
    [
      "Alvo: #{require_text(target['label'], "#{target_id}.target.label")}",
      stage_text(target_file, 'thumbnail', target_id)
    ].join("\n")
  end

  payload['thumbnail_prompt'] = prompt_block(
    'Camada geral',
    general_thumbnail,
    'Camada do canal de destino',
    channel_thumbnail,
    'Use somente a regra correspondente ao formato informado pelo pipeline.',
    thumbnail_rules.join("\n\n")
  )

  required_fields = %w[
    slug name niche niche_aliases active selection_short_prompt
    selection_long_prompt metadata_short_prompt metadata_long_prompt thumbnail_prompt
  ]
  required_fields.each { |field| abort "Campo DB inválido: #{field}" if payload[field].nil? }

  output_path = File.join(options[:output_dir], "#{slug}.json")
  File.write(output_path, JSON.pretty_generate(payload) + "\n")
  compiled_slugs[slug] = true
  puts "Gerado #{output_path}"
end
