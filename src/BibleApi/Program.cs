using BibleApi.Configuration;
using BibleApi.Services;
using Microsoft.Extensions.Caching.Memory;

var builder = WebApplication.CreateBuilder(args);

// Add configuration
builder.Services.Configure<AppSettings>(builder.Configuration.GetSection("AppSettings"));

// Add services to the container
builder.Services.AddControllers();

// Add memory caching for performance
builder.Services.AddMemoryCache();

// Add response compression for better performance
builder.Services.AddResponseCompression(options =>
{
    options.EnableForHttps = true;
    options.Providers.Add<Microsoft.AspNetCore.ResponseCompression.GzipCompressionProvider>();
});

// Register Bible service based on configuration availability
var appSettings = builder.Configuration.GetSection("AppSettings").Get<AppSettings>();
if (string.IsNullOrEmpty(appSettings?.AzureStorageConnectionString) && builder.Environment.IsDevelopment())
{
    // Register the actual service
    builder.Services.AddScoped<MockAzureXmlBibleService>();
    // Wrap it with caching
    builder.Services.AddScoped<IAzureXmlBibleService>(provider =>
        new CachedBibleService(
            provider.GetRequiredService<MockAzureXmlBibleService>(),
            provider.GetRequiredService<IMemoryCache>(),
            provider.GetRequiredService<ILogger<CachedBibleService>>()));
}
else
{
    // Register the actual service
    builder.Services.AddScoped<AzureXmlBibleService>();
    // Wrap it with caching
    builder.Services.AddScoped<IAzureXmlBibleService>(provider =>
        new CachedBibleService(
            provider.GetRequiredService<AzureXmlBibleService>(),
            provider.GetRequiredService<IMemoryCache>(),
            provider.GetRequiredService<ILogger<CachedBibleService>>()));
}

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .WithMethods("GET", "OPTIONS")
              .WithHeaders("Content-Type");
    });
});

// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { 
        Title = "Bible API", 
        Version = "v1",
        Description = "A JSON API for Bible verses and passages"
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

// Add CORS middleware
app.UseCors();

// Add response compression
app.UseResponseCompression();

// Enhanced health check endpoint
app.MapGet("/healthz", async (IAzureXmlBibleService bibleService) =>
{
    try
    {
        // Test service availability
        var translations = await bibleService.ListTranslationsAsync();
        var isHealthy = translations?.Any() == true;
        
        var response = new
        {
            status = isHealthy ? "healthy" : "degraded",
            timestamp = DateTime.UtcNow,
            version = "1.0.0",
            environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Unknown",
            checks = new
            {
                bible_service = isHealthy ? "healthy" : "degraded",
                translations_count = translations?.Count ?? 0
            }
        };
        
        return isHealthy ? Results.Ok(response) : Results.StatusCode(503);
    }
    catch (Exception ex)
    {
        var errorResponse = new
        {
            status = "unhealthy",
            timestamp = DateTime.UtcNow,
            error = ex.Message,
            environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") ?? "Unknown"
        };
        return Results.Json(errorResponse, statusCode: 503);
    }
});

// Favicon endpoint
app.MapGet("/favicon.ico", () => Results.StatusCode(204));

app.UseAuthorization();

app.MapControllers();

app.Run();
