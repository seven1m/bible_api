FROM ruby:3.1.4-alpine

# Install dependencies
RUN apk add --no-cache git curl build-base mariadb-client mariadb-dev redis

# Clone the repo
RUN git clone https://github.com/seven1m/bible_api
WORKDIR /bible_api
RUN git submodule update --init

# Install Ruby dependencies
RUN gem install bundler
RUN bundle config --local deployment true
RUN bundle install

# Set environment variables
ENV DATABASE_URL="mysql2://user:password@localhost/bible_api"
ENV REDIS_URL="redis://localhost:6379"

# Create the database and import the translations
RUN mysql -uroot -e "create database bible_api; grant all on bible_api.* to user@localhost identified by 'password';" && \
    bundle exec ruby import.rb

# Expose the necessary port (replace 3000 with the actual port your application uses)
EXPOSE 3000

# Start the application
CMD ["bundle", "exec", "ruby", "app.rb"]