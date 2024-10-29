library(ggplot2)
library(ggrepel)

merged <- read.csv("Data/Tags/tag_merged.csv")
merged_top50 <- head(merged, 50)

p <- ggplot(merged_top50, aes(x = Mean_Number_of_Ratings, y = Mean_Rating)) +
  geom_point(color = "purple", alpha = 0.6, size = 3) +  # 绘制散点
  geom_text_repel(aes(label = Tag),  # 使用geom_text_repel自动调整标签位置
                  size = 3,
                  box.padding = 0.35,  # 文字与点之间的距离
                  point.padding = 0.3,  # 点与标签之间的距离
                  segment.color = 'grey50',  # 连接线的颜色
                  max.overlaps = 5) +  # 允许的最大重叠数
  theme_minimal() +  # 设置最小主题
  labs(
    title = "50 Tags by Mean Number of Ratings and Mean Rating",
    x = "Mean Number of Ratings",
    y = "Mean Rating"
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),  # 设置标题样式
    axis.title = element_text(size = 12)
  )

p2 <- ggplot(merged_top50, aes(x = Number_of_Ratings, y = Mean_Rating)) +
  geom_point(color = "purple", alpha = 0.6, size = 3) +  # 绘制散点
  geom_text_repel(aes(label = Tag),  # 使用geom_text_repel自动调整标签位置
                  size = 3,
                  box.padding = 0.35,  # 文字与点之间的距离
                  point.padding = 0.3,  # 点与标签之间的距离
                  segment.color = 'grey50',  # 连接线的颜色
                  max.overlaps = 5) +  # 允许的最大重叠数
  theme_minimal() +  # 设置最小主题
  labs(
    title = "50 Tags by Mean Number of Ratings and Mean Rating",
    x = "Mean Number of Ratings",
    y = "Mean Rating"
  ) +
  theme(
    plot.title = element_text(hjust = 0.5, size = 14, face = "bold"),  # 设置标题样式
    axis.title = element_text(size = 12)
  )

merged_top50$Number_of_Ratings_Z <- scale(merged_top50$Number_of_Ratings)
median_value <- median(merged_top50$Number_of_Ratings)
iqr_value <- IQR(merged_top50$Number_of_Ratings)
merged_top50$Number_of_Ratings_Robust <- (merged_top50$Number_of_Ratings-median_value)/iqr_value

ggsave(p, filename ="TagsbyMeanNumberofRatingsandMeanRating.png", width = 10, height = 8, dpi = 300)
