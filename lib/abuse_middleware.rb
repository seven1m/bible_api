require 'redis'

class Rack::AbuseMiddleware
  def initialize(app, options = {})
    @app = app
    @redis = options.fetch(:redis)
    @limit = options[:limit] || 10
    @window = options[:window] || 30
    @block_time = options[:block_time] || 3600
  end

  def call(env)
    ip = (env['HTTP_X_FORWARDED_FOR'] || env['REMOTE_ADDR']).to_s.split(',').first
    key_404 = "ips:#{ip}:404s"
    key_blocked = "ips:#{ip}:blocked"

    return 403, { 'content-type' => 'text/plain' }, ["Forbidden\n"] if @redis.exists(key_blocked) == 1

    status, headers, body = @app.call(env)

    if status == 404
      count = @redis.incr(key_404)
      @redis.expire(key_404, @window) if count == 1

      if count > @limit
        @redis.set(key_blocked, '1', ex: @block_time)
        return 403, { 'content-type' => 'text/plain' }, ["Forbidden\n"]
      end
    end

    [status, headers, body]
  end
end
