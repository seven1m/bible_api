using BibleApi.Configuration;
using BibleApi.Services;

var builder = WebApplication.CreateBuilder(args);

// Add configuration
builder.Services.Configure<AppSettings>(builder.Configuration.GetSection("AppSettings"));

// Add services to the container
builder.Services.AddControllers();
builder.Services.AddScoped<IAzureXmlBibleService, AzureXmlBibleService>();

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

// Health check endpoint
app.MapGet("/healthz", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

// Favicon endpoint
app.MapGet("/favicon.ico", () => Results.StatusCode(204));

app.UseAuthorization();

app.MapControllers();

app.Run();
